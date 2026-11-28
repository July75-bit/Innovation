"""每日自动结算：让价格历史"随时间生长"（方案 A）。

负责人：B + C 链路代做（2026-11-28）

**解决什么问题**：线上 `price_history` 只有 bootstrap 一次性灌入的批次数据
（10-31 基准 + 前 11 轮，最后一点停在 11-11），此后没有任何机制推进价格：
- `GET /api/players/{id}/prices` 只查表；
- `POST /api/prices/recalc` 是运维接口，需要有人提交本轮 (score, S) + RESEED_TOKEN；
- `render.yaml` 里唯一的 cron（agent_patrol）明确只读、不产价格。

**本脚本干什么**（每天由 Render cron 跑一次，也可手动）：
1. 问后端"已落库的最新日期"（全选手 price_history.ts 的最大值）→ 折算已结算轮次；
2. 用与 `scripts/simulate_match.py` **完全相同的状态机**（同 seed/窗口/回填）从第 1 轮
   重放到今天：保证补交的 S(t) 与 bootstrap 当时会算出的完全一致，新曲线与
   线上已有点位无缝衔接；
3. 把未落库的轮次逐轮 `POST /api/prices/recalc?token=...`；
4. recalc 按 (player_id, 比赛日) 幂等 → cron 重跑、故障多日后补跑都安全（重复轮返回 skipped）。

**赛季滚轮规则**：赛程文件 28 轮（2026-11-01 ~ 11-28）。第 29 轮起沿用
`core_engine.schedule` 的圆桌循环对阵（`round_match` 取模），比赛日期按
`start + (round-1)` 天顺延 → 演示季"永不过季"，曲线每天照涨。

**2026-11-28 调整（免费档没有 cron）**：`playerstock-price-settle` 已从 render.yaml
移除，"每天自动"改为**后端惰性自结算**（`app/core/auto_settle.py`，`AUTO_SETTLE=1`，
冷启动 / 访问市场或行情接口时顺路补到期轮次，链条与本脚本完全一致）。
本脚本保留用途：① 运维手动补结算；② 升级付费档恢复 cron 或改用 GitHub Actions 定时时的参考实现。

用法（仓库根）：
    python scripts/settle_round.py --dry-run        # 只打印将补哪些轮、每轮交谁
    python scripts/settle_round.py                  # 实际结算（需要 BACKEND_BASE_URL / RESEED_TOKEN）
    python scripts/settle_round.py --to-round 15    # 手动只补到第 15 轮
    python scripts/settle_round.py --base-url http://127.0.0.1:8123 --token xxx   # 本地联调

Render 环境变量：BACKEND_BASE_URL、RESEED_TOKEN（render.yaml 里 fromService 引用后端）、
可选 SETTLE_SEED(42) / SETTLE_WINDOW(5) / SETTLE_WARMUP(3) / SETTLE_START_DATE(2026-11-01) /
SETTLE_HEALTH_TIMEOUT(150 秒，等冷启动的预算)。

退出码：0 = 成功（含"已最新，无需补"）；1 = 配置缺失或接口失败。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台中文不乱码
    except Exception:  # noqa: BLE001
        pass

from core_engine import (  # noqa: E402
    generate_match,
    load_schedule,
    standardize_score,
    suspension_reason,
)

SEED_FILE = ROOT / "data" / "seed_players.json"
DEFAULT_BASE = "https://playerstock-backend-mdlk.onrender.com"
USER_AGENT = "playerstock-settle/1.0 (+course project)"


# ---------------------------------------------------------------- 纯日期换算
def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def play_date(start: date, round_no: int) -> date:
    """轮次 → 比赛日（UTC）：第 1 轮 = 赛季首日，之后每日一轮（超出赛程顺延）。"""
    return start + timedelta(days=round_no - 1)


def round_on_day(start: date, day: date) -> int:
    """日期 → 轮次；早于赛季返回 0（= 还没结算过任何轮）。"""
    return max(0, (day - start).days + 1)


# ---------------------------------------------------------------- HTTP 小工具
def http_json(method: str, url: str, payload: dict | None = None, timeout: float = 60.0) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {}


def wait_backend(base: str, timeout_s: float) -> None:
    """免费实例可能正在休眠：轮询 /api/health 直到唤醒（冷启动约 30 秒）。"""
    deadline = time.monotonic() + timeout_s
    attempt = 0
    while True:
        attempt += 1
        try:
            health = http_json("GET", f"{base}/api/health", timeout=30)
            print(f"[settle] 后端在线：{health.get('status', 'ok')}（尝试 {attempt} 次）")
            return
        except Exception as exc:  # noqa: BLE001
            if time.monotonic() >= deadline:
                raise RuntimeError(f"后端 {timeout_s:.0f} 秒内未上线：{exc}") from exc
            print(f"[settle] 等待后端唤醒……（{type(exc).__name__}）")
            time.sleep(5)


# ---------------------------------------------------------------- 进度探测
def latest_settled_round(
    base: str, player_ids: list[int], start: date
) -> tuple[int, str]:
    """逐个拉选手价格历史，取全库最大 ts → 已结算到第几轮。

    为什么看全部选手：每轮有两支队（4 人）停牌、当天没有新点，只看一人会低估进度。
    就算低估了也安全：recalc 幂等，最坏是无害重放（applied=0, all skipped）。
    """
    latest = ""
    for pid in player_ids:
        points = http_json("GET", f"{base}/api/players/{pid}/prices").get("points", [])
        if points:
            ts = str(points[-1]["ts"])  # 契约保证升序，末位即最大
            if ts > latest:
                latest = ts
    if not latest:
        return 0, ""
    day = datetime.fromisoformat(latest.replace("Z", "+00:00")).date()
    return round_on_day(start, day), latest


# ---------------------------------------------------------------- 状态机（与 simulate_match 同源）
def warmup_scores(player: dict, seed: int, count: int) -> list[float]:
    """负数轮次回填最近 count 场评分（与 simulate_match.warmup_history 逐字对应）。"""
    return [
        generate_match(
            player["player_id"],
            seed=seed,
            round_no=n,
            base_rating=float(player["rating"]),
        ).score
        for n in range(-count, 0)
    ]


def build_payloads(
    players: list[dict],
    schedule: dict,
    *,
    start: date,
    seed: int,
    window: int,
    warmup: int,
    first: int,
    target: int,
) -> list[dict]:
    """重放第 1..target 轮（决定 S(t) 的链条），返回 first..target 轮的 recalc 请求体。

    停牌处理与 simulate_match._process_match 一致：整队比赛 → 本轮该选手不出现在 items、
    也不进历史窗口（recalc 服务端同样会跳过，这里只是少传冗余数据）。
    """
    state = {p["player_id"]: warmup_scores(p, seed, warmup) for p in players}
    payloads: list[dict] = []
    for round_no in range(1, target + 1):
        day = play_date(start, round_no).isoformat()
        items: list[dict] = []
        for p in players:
            match = generate_match(
                p["player_id"],
                seed=seed,
                round_no=round_no,
                played_at=day,
                base_rating=float(p["rating"]),
            )
            if suspension_reason(p, round_no, schedule):
                continue
            history = state[p["player_id"]]
            signal = standardize_score(match.score, history, window=window)
            history.append(match.score)
            items.append({"player_id": p["player_id"], "score": match.score, "signal": signal})
        if round_no >= first and items:
            payloads.append({"round_no": round_no, "played_at": day, "items": items})
    return payloads


# ---------------------------------------------------------------- 提交
def post_all(base: str, token: str, payloads: list[dict]) -> int:
    """逐轮 POST /api/prices/recalc；返回失败轮数（403 视为口令问题，立即止损）。"""
    qs = urllib.parse.urlencode({"token": token})
    failures = 0
    for payload in payloads:
        url = f"{base}/api/prices/recalc?{qs}"
        try:
            resp = http_json("POST", url, payload)
        except urllib.error.HTTPError as exc:
            failures += 1
            body = exc.read().decode("utf-8", "replace")[:200]
            print(f"[settle] ✗ 第 {payload['round_no']} 轮 HTTP {exc.code}: {body}")
            if exc.code == 403:
                print("[settle] ✗ 口令被拒（OPS_TOKEN_UNSET / TOKEN_MISMATCH），停止后续轮次")
                break
            continue
        applied, skipped = resp.get("applied", []), resp.get("skipped", [])
        sample = applied[0] if applied else None
        hint = (
            f"，例：#{sample['player_id']} {sample['old_price']}→{sample['new_price']}"
            f"（{sample['change_pct']:+.2f}%）"
            if sample
            else ""
        )
        print(f"[settle] 第 {payload['round_no']} 轮 · {payload['played_at']}："
              f"计价 {len(applied)} 人、跳过 {len(skipped)} 人{hint}")
    return failures


# ---------------------------------------------------------------- CLI 与编排
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按日期自动补结算价格历史（方案 A 的 cron 入口）")
    parser.add_argument("--base-url", default=None, help="后端地址（默认 env BACKEND_BASE_URL）")
    parser.add_argument("--token", default=None, help="运维口令（默认 env RESEED_TOKEN）")
    parser.add_argument("--seed", type=int, default=None, help="模拟种子（默认 env SETTLE_SEED=42）")
    parser.add_argument("--window", type=int, default=None, help="标准化窗口（默认 env SETTLE_WINDOW=5）")
    parser.add_argument("--warmup", type=int, default=None, help="回填历史场次（默认 env SETTLE_WARMUP=3）")
    parser.add_argument("--from-round", type=int, default=None, help="强制从第几轮补（默认自动探测）")
    parser.add_argument("--to-round", type=int, default=None, help="强制补到第几轮（默认补到今天）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不 POST")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base = (args.base_url or os.getenv("BACKEND_BASE_URL", DEFAULT_BASE)).rstrip("/")
    token = args.token or os.getenv("RESEED_TOKEN", "")
    start = date.fromisoformat(os.getenv("SETTLE_START_DATE", "2026-11-01"))
    seed = args.seed if args.seed is not None else int(os.getenv("SETTLE_SEED", "42"))
    window = args.window if args.window is not None else int(os.getenv("SETTLE_WINDOW", "5"))
    warmup = args.warmup if args.warmup is not None else int(os.getenv("SETTLE_WARMUP", "3"))
    health_timeout = float(os.getenv("SETTLE_HEALTH_TIMEOUT", "150"))

    if not SEED_FILE.exists():
        print(f"[settle] ✗ 找不到 {SEED_FILE}")
        return 1
    players = json.loads(SEED_FILE.read_text(encoding="utf-8"))["players"]
    schedule = load_schedule()

    print(f"[settle] 目标后端：{base}（seed={seed}, window={window}, warmup={warmup}）")
    wait_backend(base, health_timeout)

    last, latest_ts = latest_settled_round(base, [p["player_id"] for p in players], start)
    target = args.to_round if args.to_round is not None else round_on_day(start, utc_today())
    first = args.from_round if args.from_round is not None else last + 1
    print(f"[settle] 已落库最新点：{latest_ts or '（空库）'} → 已结算到第 {last} 轮；"
          f"今天是第 {round_on_day(start, utc_today())} 轮；本次拟补第 {first}–{target} 轮")
    if first > target:
        print("[settle] 已追平到最新轮次，无需补结算")
        return 0

    payloads = build_payloads(
        players, schedule, start=start, seed=seed, window=window,
        warmup=warmup, first=first, target=target,
    )

    if args.dry_run:
        for payload in payloads:
            ids = ",".join(str(i["player_id"]) for i in payload["items"])
            print(f"[dry-run] 第 {payload['round_no']} 轮 · {payload['played_at']}："
                  f"{len(payload['items'])} 人（player_id: {ids}）")
        print(f"[dry-run] 共 {len(payloads)} 轮待结算（未发送任何请求）")
        return 0

    if not token:
        print("[settle] ✗ 缺少运维口令：设 RESEED_TOKEN 或传 --token（dry-run 不需要）")
        return 1

    failures = post_all(base, token, payloads)
    last2, latest_ts2 = latest_settled_round(base, [p["player_id"] for p in players], start)
    print(f"[settle] 完成：失败 {failures} 轮；库内最新点已到 {latest_ts2 or '（空）'}（第 {last2} 轮）")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
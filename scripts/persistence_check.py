"""重新部署前后「数据是否仍在」的自动对账（第 6 天，B）。

负责人：B

**为什么不是截图**：截图能看，但没法验证，还会被压糊。这个脚本做的是同一件事的更硬版本——
把 `/api/account`、`/api/trades`、`/api/players/{id}/prices` 的**原始响应**按时间戳存成 JSON，
再逐项 diff。任何人拿这两个 JSON 重跑 `--diff` 都能得到同一张表。

用法：

    # 部署前
    python scripts/persistence_check.py --base https://playerstock-backend-mdlk.onrender.com \
        --out .tmp/persist-before.json --label before

    # Render 点完 Manual Deploy、服务变 Live 之后
    python scripts/persistence_check.py --base https://playerstock-backend-mdlk.onrender.com \
        --out .tmp/persist-after.json --label after

    # 对账（不一致时退出码 1）
    python scripts/persistence_check.py --diff .tmp/persist-before.json .tmp/persist-after.json

注意：
- **不要**在两个快照之间跑 `bootstrap_demo_data.py --reset`，那会把数据重置，证明不了"数据还在"；
- 部署期间线上短暂 5xx 属正常，脚本会重试，别在同一秒硬打。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

DEFAULT_PLAYER = 1
RETRY = 5


def fetch(base: str, path: str, retry: int = RETRY) -> tuple[int, object]:
    """带重试的 GET：部署窗口里 502/超时都当"还没起来"。"""
    last_error = ""
    for attempt in range(1, retry + 1):
        try:
            with httpx.Client(base_url=base.rstrip("/"), timeout=30.0) as client:
                resp = client.get(path)
            if resp.status_code < 500:
                return resp.status_code, resp.json()
            last_error = f"HTTP {resp.status_code}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        print(f"    [{attempt}/{retry}] {path} 还没起来（{last_error}），2s 后重试…", flush=True)
        time.sleep(2)
    raise SystemExit(f"[persist] 放弃：{path} 连续 {retry} 次失败（{last_error}）")


def snapshot(base: str, player_id: int, label: str) -> dict:
    print(f"[persist] 采集快照（{label}）…", flush=True)
    status_account, account = fetch(base, "/api/account")
    status_trades, trades = fetch(base, "/api/trades")
    status_prices, prices = fetch(base, f"/api/players/{player_id}/prices")
    status_players, players = fetch(base, "/api/players")

    points = prices.get("points", []) if isinstance(prices, dict) else prices
    payload = {
        "label": label,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base": base.rstrip("/"),
        "player_id": player_id,
        "status": {
            "account": status_account,
            "trades": status_trades,
            "prices": status_prices,
            "players": status_players,
        },
        "account": account,
        "trades": trades,
        "prices": points,
        "players": players,
    }
    print(
        f"  余额 {account['balance']}；流水 {len(trades)} 条；"
        f"#{player_id} 价格点 {len(points)} 个；选手 {len(players)} 名"
    )
    return payload


def summary(snap: dict) -> dict:
    """只留"该在部署前后保持一致"的字段（价格点的 ts/price/reason 全部参与比较）。"""
    account = snap["account"]
    points = snap["prices"]
    return {
        "余额": account["balance"],
        "总资产": account["total_asset"],
        "持仓市值": account["position_value"],
        "流水条数": len(snap["trades"]),
        "流水明细": [
            (t["trade_id"], t["player_id"], t["side"], t["quantity"], t["price"], t["balance_after"])
            for t in sorted(snap["trades"], key=lambda x: x["trade_id"])
        ],
        "价格点数": len(points),
        "末点价格": points[-1]["price"] if points else None,
        "价格点签名": [(p["ts"], p["price"]) for p in points],
        "选手数": len(snap["players"]),
    }


def diff(before_path: Path, after_path: Path) -> int:
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    b, a = summary(before), summary(after)

    print(f"[persist] 部署前：{before['label']} @ {before['collected_at']}")
    print(f"[persist] 部署后：{after['label']} @ {after['collected_at']}")
    print(f"[persist] 服务：{before['base']}")
    print()
    print("| 项 | 部署前 | 部署后 | 结论 |")
    print("| --- | --- | --- | --- |")

    ok = True
    for key in ("余额", "总资产", "持仓市值", "流水条数", "价格点数", "末点价格", "选手数"):
        same = b[key] == a[key]
        ok = ok and same
        flag = "✅ 一致" if same else "❌ **不一致**"
        print(f"| {key} | {b[key]} | {a[key]} | {flag} |")

    same_rows = b["流水明细"] == a["流水明细"]
    ok = ok and same_rows
    print(f"| 流水明细（逐行 id/方向/数量/价格/余额） | {len(b['流水明细'])} 行 | {len(a['流水明细'])} 行 | "
          f"{'✅ 逐行一致' if same_rows else '❌ **不一致**'} |")

    same_points = b["价格点签名"] == a["价格点签名"]
    ok = ok and same_points
    print(f"| 价格点（逐点 ts+price） | {len(b['价格点签名'])} 点 | {len(a['价格点签名'])} 点 | "
          f"{'✅ 逐点一致' if same_points else '❌ **不一致**'} |")

    print()
    if ok:
        print("[persist] ✅ 结论：重新部署前后各项完全一致 → 线上用的是持久化数据库（Postgres），不是临时盘。")
        return 0

    print("[persist] ❌ 结论：有项目不一致！")
    print("  排查顺序：① 后端日志搜『当前部署在 Render 上却使用本地 SQLite』；② 看 DATABASE_URL 是否指向 Postgres；")
    print("  ③ 确认两次快照之间没有人跑过 bootstrap_demo_data.py --reset。")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="重新部署前后数据一致性对账")
    parser.add_argument("--base", default="https://playerstock-backend-mdlk.onrender.com")
    parser.add_argument("--player-id", type=int, default=DEFAULT_PLAYER)
    parser.add_argument("--out", type=Path, help="快照输出文件（默认 .tmp/persist-<label>.json）")
    parser.add_argument("--label", default="snapshot")
    parser.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"), help="对账两个快照")
    args = parser.parse_args()

    if args.diff:
        return diff(Path(args.diff[0]), Path(args.diff[1]))

    snap = snapshot(args.base, args.player_id, args.label)
    out = args.out or Path(".tmp") / f"persist-{args.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[persist] 已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

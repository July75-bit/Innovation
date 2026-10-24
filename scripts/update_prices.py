"""价格更新落库脚本（T3-01）：C 只算，B 写库。

负责人：B（写库） / C（模拟比赛 + 定价公式）

分工见 `code/backend/app/core/price_update.py` 与 `docs/software/database_design.md` §3.2：

- **C 只算**：`core_engine.simulator.generate_match()` 造比赛 →
  `core_engine.pricing.standardize_score()` 算 S(t) → `update_price()` 出
  `PriceUpdate(new_price, change_pct, reason)`，一律不碰数据库；
- **B 写库**：本脚本把结果塞进同一个事务，写
  `players.current_price/prev_price` + `price_history`，
  **永不碰 `users.balance` / `positions`**。

用法（仓库根目录）：

    python scripts/update_prices.py                       # 可交易选手各更新一次价格
    python scripts/update_prices.py --dry-run             # 只看不写
    python scripts/update_prices.py --rounds 3 --seed 42  # 同一 seed 完全可复现
    python scripts/update_prices.py --player-id 1
    python scripts/update_prices.py --from-json data/price_updates.json

两条入口，同一套落库逻辑：

1. **默认（进程内）**：直接调 C 的 `simulator` + `pricing`，约定与
   `scripts/simulate_match.py` 完全一致（`--warmup` 用负数轮次回填内存历史、
   `--window` 默认 5、基准评分取 `players.rating`），保证两边算出来的数一样。
2. **`--from-json`**：吃 C 的 `python scripts/simulate_match.py --json <file>` 导出的明细。
   C 调模型不用等 B，B 落库也不用懂模型。

两条约定：

- **暂停交易（`status != trading`）的选手不定价**，与买卖规则一致；
- `reason` 末尾统一带"本轮模拟得分"，让每条历史价格都能追溯到是哪场表现算出来的
  （第 3 天决策：不新增 `matches` 表，靠 `reason` 保持可解释性）。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))
sys.path.insert(0, str(ROOT / "code"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台中文不乱码
    except Exception:  # noqa: BLE001 - 被 pytest 捕获时 stdout 可能不支持重配置
        pass

TRADING_STATUS = "trading"
MAX_REASON_LENGTH = 200


# ---------------------------------------------------------------- 把 C 的结果接进来
def warmup_history(
    player_id: int, base_rating: float, count: int, seed: int
) -> list[float]:
    """用负数轮次回填最近 N 场评分（与 `simulate_match.py` 同约定，只在内存）。"""
    if count <= 0:
        return []
    from core_engine import generate_match

    return [
        generate_match(
            player_id, seed=seed, round_no=round_no, base_rating=base_rating
        ).score
        for round_no in range(-count, 0)
    ]


def with_score_in_reason(reason: str, score: float) -> str:
    """把本轮得分补进 reason，保证一条历史价格能追溯到具体表现。

    C 的 reason 已经带了 S(t) 和涨跌幅，这里只补"得分"这一项缺失的上下文。

    **这层拼接是临时的**（见 `database_design.md` §3.2「分工待办」）：得分本来在 C 手里，
    约定由 C 直接在 `update_price` 的 `reason` 里拼好；C 改完后删掉本函数、
    B 只做透传即可。
    """
    text = f"{reason}（本轮模拟得分 {score:.1f}）"
    if len(text) > MAX_REASON_LENGTH:
        # price_history.reason 是 VARCHAR(200)，宁可截断也不能写库失败
        text = text[: MAX_REASON_LENGTH - 1] + "…"
    return text


def plan_from_engine(
    players, *, seed: int = 42, window: int = 5, warmup: int = 3, rounds: int = 1
):
    """进程内调 C 的模拟比赛 + 定价引擎，算出每名可交易选手的待落库变化。"""
    from core_engine import generate_match, standardize_score, update_price

    from app.core.price_update import plan_for_player

    planned = []
    skipped = []
    for player in players:
        if player.status != TRADING_STATUS:
            skipped.append(player)
            continue

        base_rating = float(player.rating)
        history = warmup_history(player.player_id, base_rating, warmup, seed)

        result = None
        last_score = 0.0
        for round_no in range(1, max(rounds, 1) + 1):
            match = generate_match(
                player.player_id, seed=seed, round_no=round_no, base_rating=base_rating
            )
            signal = standardize_score(match.score, history, window=window)
            result = update_price(float(player.current_price), signal)
            history.append(match.score)
            last_score = match.score

        def _calc(current_price, _result=result, _score=last_score):
            return replace(
                _result, reason=with_score_in_reason(_result.reason, _score)
            )

        planned.append(plan_for_player(player, _calc))

    return planned, skipped


def plan_from_json(path: str | Path, name_by_id: dict[int, str] | None = None):
    """吃 C 的 `--json` 导出：`{updates: [{player_id, score, reason, new_price, ts, ...}]}`。"""
    from app.core.price_update import PlannedUpdate

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("updates") or []
    if not rows:
        raise ValueError(
            f"{path} 里没有 updates，先跑 python scripts/simulate_match.py --json <file>"
        )

    names = name_by_id or {}
    planned = []
    for row in rows:
        player_id = int(row["player_id"])
        new_price = Decimal(str(row["new_price"]))
        if new_price <= 0:
            raise ValueError(f"选手 {player_id} 的新价非法：{new_price}")

        ts_raw = row.get("ts")
        planned.append(
            PlannedUpdate(
                player_id=player_id,
                name=names.get(player_id, f"#{player_id}"),
                old_price=Decimal(str(row["old_price"])),
                new_price=new_price,
                change_pct=float(row["change_pct"]),
                reason=with_score_in_reason(
                    str(row.get("reason", "")), float(row["score"])
                ),
                ts=datetime.fromisoformat(ts_raw) if ts_raw else None,
            )
        )
    return planned


# ---------------------------------------------------------------- 主流程
def run(args: argparse.Namespace) -> int:
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.core.price_update import apply_updates, price_history_count
    from app.models import Player

    with SessionLocal() as db:
        stmt = select(Player).order_by(Player.player_id)
        if args.player_id is not None:
            stmt = stmt.where(Player.player_id == args.player_id)
        players = list(db.scalars(stmt).all())
        if not players:
            print(
                "[update_prices] 没有找到选手（--player-id="
                f"{args.player_id}），先跑 python scripts/seed_db.py"
            )
            return 2

        name_by_id = {p.player_id: p.name for p in players}

        if args.from_json:
            planned = plan_from_json(args.from_json, name_by_id)
            if args.player_id is not None:
                planned = [p for p in planned if p.player_id == args.player_id]
            skipped = []
            engine_line = f"C 导出的明细（{args.from_json}）"
        else:
            planned, skipped = plan_from_engine(
                players,
                seed=args.seed,
                window=args.window,
                warmup=args.warmup,
                rounds=args.rounds,
            )
            engine_line = (
                f"core_engine.update_price（seed={args.seed}，window={args.window}，"
                f"warmup={args.warmup}，rounds={args.rounds}）"
            )

        if not planned:
            print("[update_prices] 没有需要更新的选手（全部非 trading？）")
            return 0

        print(f"[update_prices] 数据库：{db.get_bind().url}")
        print(f"[update_prices] 引擎：{engine_line}")
        for item in planned:
            print("  " + item.display)
        if skipped:
            names = "、".join(p.name for p in skipped)
            print(f"[update_prices] 跳过 {len(skipped)} 名非 trading 选手：{names}")

        if args.dry_run:
            print("[update_prices] --dry-run：以上仅为预览，没有写库")
            return 0

        apply_updates(db, planned)
        print("[update_prices] 已提交（players.current_price/prev_price + price_history 同事务）")
        for player_id in sorted({item.player_id for item in planned}):
            name = name_by_id.get(player_id, f"#{player_id}")
            print(f"  {name}: price_history 现有 {price_history_count(db, player_id)} 条")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="把 C 的定价结果写进数据库（T3-01）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（演示必须固定）")
    parser.add_argument("--window", type=int, default=5, help="标准化窗口 N（默认 5 场）")
    parser.add_argument(
        "--warmup", type=int, default=3, help="开赛前回填最近 N 场历史评分（默认 3，只在内存）"
    )
    parser.add_argument(
        "--rounds", type=int, default=1, help="生成几轮比赛，取最后一轮定价（默认 1）"
    )
    parser.add_argument("--player-id", type=int, default=None, help="只更新指定选手")
    parser.add_argument(
        "--from-json", type=str, default=None, help="用 C 导出的明细文件落库"
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写库")
    args = parser.parse_args()

    sys.exit(run(args))


if __name__ == "__main__":
    main()

"""价格更新落库脚本（T3-01）：调用 C 的定价函数，把结果写进库。

负责人：B（写库） / C（公式）

分工见 `code/backend/app/core/price_update.py` 与 `docs/software/database_design.md` §3.2：
C 只算 `PriceUpdate(new_price, change_pct, reason)`，B 在同一事务里写
`players.current_price/prev_price` + `price_history`，**永不碰 `users.balance` / `positions`**。

用法（仓库根目录）：

    python scripts/update_prices.py                     # 全部选手，自动选引擎
    python scripts/update_prices.py --dry-run            # 只打印，不写库
    python scripts/update_prices.py --player-id 1 --seed 42
    python scripts/update_prices.py --engine pricing --score 0.42 --player-id 1
    python scripts/update_prices.py --engine stub        # 强制用临时规则

引擎说明：

- `pricing`：用 C 的 `code/core_engine/pricing.py::update_price`。需要 `--score`（S(t)），
  因为比赛数据发生器（C 的 `simulator.py`）还没实现，暂时没有别的地方能给出 S。
- `stub`：**临时规则**，按 `docs/algorithm/pricing_model.md` 的公式自己算，
  表现信号 S 用固定种子伪随机生成（同 seed 两次结果完全一致）。
  目的是让第 3 天的联调有价格变化可看。
- `auto`（默认）：先试 `pricing`，遇到 `NotImplementedError` 自动回落到 `stub` 并提示。

> `--engine stub` 与 `_temporary_price_rule()` 是**临时脚手架**：C 的 `update_price`
> 与 `simulator.py` 就绪后，直接删掉这两处，脚本行为不变（走 `pricing` 分支）。
"""

from __future__ import annotations

import argparse
import random
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))

CENT = Decimal("0.01")
CLAMP_PCT = Decimal("20")  # 单次最大涨跌幅 ±20%（pricing_model.md 的 clamp 定值）


# ---------------------------------------------------------------- 引擎
def _temporary_price_rule(current_price: Decimal, score_delta: float) -> object:
    """临时定价规则（C 的 `update_price` 未就绪时保联调用）。

    公式照 `docs/algorithm/pricing_model.md` 的方案 A：
        P' = max(floor, P × (1 + α·S + β·D))，单次变化 clamp ±20%，2 位小数
    参数从 settings 读（α=0.15 / β=0 / floor=1.0）。
    """
    from app.core.config import settings
    from core_engine.pricing import PriceUpdate

    alpha = Decimal(str(settings.pricing_alpha))
    floor = Decimal(str(settings.pricing_floor))
    beta = Decimal(str(settings.pricing_beta))
    demand = Decimal("0")  # β=0，需求项暂不启用

    raw = current_price * (Decimal(1) + alpha * Decimal(str(score_delta)) + beta * demand)
    raw = max(floor, raw)

    # clamp：单次涨跌幅不超过 ±20%
    upper = current_price * (Decimal(1) + CLAMP_PCT / Decimal(100))
    lower = current_price * (Decimal(1) - CLAMP_PCT / Decimal(100))
    new_price = min(max(raw, lower), upper).quantize(CENT, rounding=ROUND_HALF_UP)

    change_pct = ((new_price - current_price) / current_price * 100).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    direction = "提升" if score_delta > 0 else ("下滑" if score_delta < 0 else "持平")
    reason = (
        f"临时规则：模拟表现{direction}（S={score_delta:+.2f}，"
        f"定价引擎由 C 接管后替换）"
    )
    return PriceUpdate(
        new_price=float(new_price), change_pct=float(change_pct), reason=reason
    )


def _stub_score(player_id: int, seed: int) -> float:
    """固定种子伪随机的表现信号 S(t)，落在 [-0.5, 0.5]，同 seed 完全可复现。"""
    rng = random.Random(f"playerstock-{seed}-{player_id}")
    return round(rng.uniform(-0.5, 0.5), 2)


def _pricing_engine(current_price: Decimal, *, score: float | None):
    """C 的正式引擎；需要外部给 S(t)。"""
    from core_engine.pricing import update_price

    if score is None:
        raise ValueError(
            "用 --engine pricing 时必须给 --score（S(t)）；比赛数据发生器（simulator.py）"
            "还没实现，暂时没有别的地方能算出 S"
        )
    return update_price(float(current_price), score)


def _pricing_available() -> bool:
    """探测 C 的 `update_price` 是否已实现（只探一次，不按选手重复 try/except）。"""
    from core_engine.pricing import update_price

    try:
        update_price(100.0, 0.0)
    except NotImplementedError:
        return False
    except Exception:  # noqa: BLE001 - 实现了但参数有问题，交给真正调用时报错
        return True
    return True


def build_calculator(*, engine: str, seed: int, score: float | None, player_id: int):
    """返回一个 `callable(现价) -> PriceUpdate`。"""

    def _calc(current_price: Decimal):
        if engine == "stub":
            return _temporary_price_rule(current_price, _stub_score(player_id, seed))
        return _pricing_engine(current_price, score=score)

    return _calc


# ---------------------------------------------------------------- 主流程
def run(args: argparse.Namespace) -> int:
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.core.price_update import apply_updates, plan_for_player, price_history_count
    from app.models import Player

    engine = args.engine
    if engine == "auto":
        if _pricing_available() and args.score is not None:
            engine = "pricing"
        else:
            engine = "stub"
            print(
                "[update_prices] C 的定价引擎尚未就绪（update_price / simulator 仍是 "
                "NotImplementedError）或未给 --score，本次使用**临时规则**生成价格变化，"
                "仅供第 3 天联调；C 接管后本提示与临时规则一起删除。"
            )

    with SessionLocal() as db:
        stmt = select(Player).order_by(Player.player_id)
        if args.player_id is not None:
            stmt = stmt.where(Player.player_id == args.player_id)
        players = list(db.scalars(stmt).all())
        if not players:
            print(f"[update_prices] 没有找到选手（--player-id={args.player_id}），先跑 "
                  "python scripts/seed_db.py")
            return 2

        planned = []
        for player in players:
            calculator = build_calculator(
                engine=engine, seed=args.seed, score=args.score, player_id=player.player_id
            )
            planned.append(plan_for_player(player, calculator))

        print(f"[update_prices] 数据库：{db.get_bind().url}")
        print(f"[update_prices] 引擎：{engine}；共 {len(planned)} 名选手")
        for item in planned:
            print("  " + item.display)

        if args.dry_run:
            print("[update_prices] --dry-run：以上仅为预览，没有写库")
            return 0

        apply_updates(db, planned)
        print("[update_prices] 已提交（players.current_price/prev_price + price_history 同事务）")
        for item in planned:
            print(f"  {item.name}: price_history 现有 {price_history_count(db, item.player_id)} 条")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="把 C 的定价结果写进数据库（T3-01）")
    parser.add_argument(
        "--engine",
        choices=("auto", "pricing", "stub"),
        default="auto",
        help="pricing=C 的正式引擎；stub=临时规则；auto=先用正式、未实现则回落（默认）",
    )
    parser.add_argument("--seed", type=int, default=42, help="临时规则的随机种子（同 seed 可复现）")
    parser.add_argument("--score", type=float, default=None, help="--engine pricing 时的 S(t)")
    parser.add_argument("--player-id", type=int, default=None, help="只更新指定选手")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写库")
    args = parser.parse_args()

    if args.player_id is None and args.score is not None:
        print("[update_prices] 警告：--score 只对 --player-id 有意义，全部选手会共用同一个 S")

    sys.exit(run(args))


if __name__ == "__main__":
    main()

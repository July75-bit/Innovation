"""价格更新落库（T3-01）：C 只算，B 写库。

分工在第 3 天定死（day3 09:40–10:30，结论同时写进 `database_design.md` §3.2）：

- **C 只算**：`code/core_engine/pricing.py` 的 `update_price` / `standardize_score`
  返回 `PriceUpdate(new_price, change_pct, reason)`，不碰数据库；
- **B 写库**：本模块把算好的结果写进去，同一个事务里完成
  `UPDATE players SET prev_price = current_price, current_price = 新价`
  + `INSERT price_history(price, reason, ts)`；
- **边界**：本模块永不碰 `users.balance` 与 `positions`
  （见 `database_design.md` §3"价格更新只写 players 和 price_history"）。

这里刻意不含任何定价公式——公式是 C 的资产，换公式不该动写入逻辑。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import Player, PriceHistory

CENT = Decimal("0.01")
# price_history.reason 是 VARCHAR(200)
MAX_REASON_LENGTH = 200


class PriceCalculator(Protocol):
    """C 的定价函数在本模块眼里的样子：给现价，返回新价 + 涨跌幅 + 中文原因。"""

    def __call__(self, current_price: Decimal) -> Any: ...


@dataclass(frozen=True)
class PlannedUpdate:
    """一条待落库的价格变化（还没写库，便于 --dry-run 与单测）。"""

    player_id: int
    name: str
    old_price: Decimal
    new_price: Decimal
    change_pct: float
    reason: str

    @property
    def display(self) -> str:
        sign = "+" if self.change_pct >= 0 else ""
        return (
            f"{self.name}(#{self.player_id}) {self.old_price:.2f} → {self.new_price:.2f} "
            f"({sign}{self.change_pct:.2f}%) {self.reason}"
        )


def _to_cents(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def plan_for_player(player: Player, calculator: PriceCalculator) -> PlannedUpdate:
    """用 C 的定价函数算出一条待落库的变化（不写库）。"""
    if player is None:
        raise ValueError("player 不能为空")

    old_price = _to_cents(player.current_price)
    if old_price <= 0:
        raise ValueError(f"选手 {player.player_id} 的当前价非法：{old_price}")

    result = calculator(old_price)
    new_price = _to_cents(result.new_price)
    if new_price <= 0:
        # players.current_price 有 CHECK (current_price > 0)，这里提前拦住给出可读错误
        raise ValueError(
            f"选手 {player.player_id} 的新价非法：{new_price}（定价引擎必须保证 > 0）"
        )

    reason = str(result.reason or "").strip()
    if not reason:
        raise ValueError(f"选手 {player.player_id} 的价格变化缺少 reason（契约要求每条必带原因）")
    if len(reason) > MAX_REASON_LENGTH:
        raise ValueError(
            f"选手 {player.player_id} 的 reason 超过 {MAX_REASON_LENGTH} 字：{len(reason)}"
        )

    # 涨跌幅一律用落库的两个价格现算，避免和 C 的返回值对不上
    change_pct = float(
        ((new_price - old_price) / old_price * Decimal(100)).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
    )

    return PlannedUpdate(
        player_id=int(player.player_id),
        name=player.name,
        old_price=old_price,
        new_price=new_price,
        change_pct=change_pct,
        reason=reason,
    )


def plan_updates(
    players: Iterable[Player], calculator: PriceCalculator
) -> list[PlannedUpdate]:
    """对一批选手逐个算价，全部成功才返回（任何一条非法就整体失败，不写库）。"""
    return [plan_for_player(player, calculator) for player in players]


def apply_updates(
    db: Session,
    planned: Sequence[PlannedUpdate],
    *,
    ts: datetime | None = None,
) -> list[PlannedUpdate]:
    """把计划写进库：一个事务，players 与 price_history 要么全成、要么全回滚。

    `prev_price` 用 SQL 表达式 `players.current_price` 赋值，取的是数据库里
    那一刻的值，不依赖调用方读到的快照——和第 2 天交易侧的条件更新同一个思路。
    """
    if not planned:
        return []

    moment = ts or utcnow()
    try:
        for item in planned:
            db.execute(
                update(Player)
                .where(Player.player_id == item.player_id)
                .values(prev_price=Player.current_price, current_price=item.new_price)
            )
            db.add(
                PriceHistory(
                    player_id=item.player_id,
                    price=item.new_price,
                    reason=item.reason,
                    ts=moment,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return list(planned)


def touched_tables() -> tuple[str, ...]:
    """给测试与文档用：本模块只允许碰这两张表。"""
    return ("players", "price_history")


def price_history_count(db: Session, player_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(PriceHistory.price_id)).where(
                PriceHistory.player_id == player_id
            )
        )
        or 0
    )


__all__ = [
    "CENT",
    "MAX_REASON_LENGTH",
    "PlannedUpdate",
    "PriceCalculator",
    "apply_updates",
    "plan_for_player",
    "plan_updates",
    "price_history_count",
    "touched_tables",
]

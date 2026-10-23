"""交易流水（只追加，不更新、不删除）。

字段与 docs/software/database_design.md §2.4 一致：
trade_id / user_id / player_id / side(BUY/SELL) / quantity / price /
amount / balance_after / created_at。

为什么存 price 快照：选手价格以后还会变，流水必须能独立追溯"当时多少钱成交"。
索引 ix_trades_user_created(user_id, created_at) 支撑流水页倒序查询。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.user import User


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_user_created", "user_id", "created_at"),
        CheckConstraint("side IN ('BUY', 'SELL')", name="ck_trades_side"),
        CheckConstraint("quantity > 0", name="ck_trades_quantity_positive"),
        CheckConstraint("price > 0", name="ck_trades_price_positive"),
        CheckConstraint("amount >= 0", name="ck_trades_amount_non_negative"),
    )

    trade_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False
    )
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="trades")
    player: Mapped["Player"] = relationship(back_populates="trades")

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return (
            f"<Trade trade_id={self.trade_id} user_id={self.user_id} "
            f"player_id={self.player_id} side={self.side} qty={self.quantity}>"
        )

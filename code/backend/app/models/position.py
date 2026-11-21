"""持仓。

字段与 docs/software/database_design.md §2.3 一致：
position_id / user_id / player_id / quantity / avg_cost / updated_at。

约束：
- UNIQUE(user_id, player_id)：同一选手只有一行持仓；
- CHECK quantity BETWEEN 1 AND 50：卖出归零时删除该行，与应用层校验双保险。

avg_cost 用 4 位小数，减少多次买入的累计误差（接口输出时保留 2 位）。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.user import User


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("user_id", "player_id", name="uq_positions_user_player"),
        CheckConstraint(
            "quantity >= 1 AND quantity <= 50", name="ck_positions_quantity_range"
        ),
        CheckConstraint("avg_cost >= 0", name="ck_positions_avg_cost_non_negative"),
    )

    position_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="positions")
    player: Mapped["Player"] = relationship(back_populates="positions")

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return (
            f"<Position position_id={self.position_id} user_id={self.user_id} "
            f"player_id={self.player_id} qty={self.quantity} avg_cost={self.avg_cost}>"
        )

"""用户 / 虚拟账户。

字段与 docs/software/database_design.md §2.1 一致：
user_id / nickname / balance / initial_balance / created_at。
初始 5000 虚拟币，不可充值、不可提现、不可兑换。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.position import Position
    from app.models.trade import Trade


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_users_balance_non_negative"),
        CheckConstraint("initial_balance >= 0", name="ck_users_initial_balance_non_negative"),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal(settings.initial_balance)
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal(settings.initial_balance)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    positions: Mapped[list["Position"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<User user_id={self.user_id} nickname={self.nickname!r} balance={self.balance}>"

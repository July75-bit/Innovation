"""用户 / 虚拟账户。

字段与 docs/software/database_design.md §2.1 一致：
user_id / nickname / balance / initial_balance / created_at，
第 7 轮加私人账号后多两个可空列 password_hash / salt（见 app/core/security.py）。

初始 5000 信用点，不可充值、不可提现、不可兑换。

**口令列允许为 NULL**：`demo` 是历史账户，第 7 轮保留为"公共演示账户"——
没有口令、任何人未登录时都在用它（兜底分支见 app/api/deps.py）。
新注册的用户必须有口令，所以这条规则放在接口层校验，不加 CHECK 约束：
加了会让已有的 demo 行变成非法数据，线上 Postgres 上等于自找 500。
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
    from app.models.auth_token import AuthToken
    from app.models.position import Position
    from app.models.trade import Trade


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_users_balance_non_negative"),
        CheckConstraint("initial_balance >= 0", name="ck_users_initial_balance_non_negative"),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # unique：用户名就是登录凭据，重复等于两个账号互相顶掉（接口层也会先查一次给中文提示）
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal(settings.initial_balance)
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal(settings.initial_balance)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    # 口令散列与盐；公共演示账户（demo）为 NULL——它没有登录能力，只作未登录兜底
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salt: Mapped[str | None] = mapped_column(String(64), nullable=True)

    positions: Mapped[list["Position"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_public_demo(self) -> bool:
        """是否是公共演示账户（无口令的历史账户）。"""
        return self.password_hash is None

    def __repr__(self) -> str:  # pragma: no cover - 调试用（绝不带口令字段）
        return f"<User user_id={self.user_id} nickname={self.nickname!r} balance={self.balance}>"

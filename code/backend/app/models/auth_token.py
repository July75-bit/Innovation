"""访问令牌（第 7 轮：私人账号）。

只存令牌的 SHA-256（`app/core/security.hash_token`），原文只在登录/注册响应里出现一次。
过期时间由后端算（`TOKEN_TTL`），客户端改 localStorage 里的时间戳没有意义。

撤销语义：退出登录 = 删这一行。所以"退出"之后旧 token 立刻失效，
而不是前端删掉本地存储、服务端其实还认——那种假退出在共享电脑上会留后门。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.user import User


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tokens")

    def __repr__(self) -> str:  # pragma: no cover - 调试用（绝不打印 token_hash）
        return f"<AuthToken user_id={self.user_id} expires_at={self.expires_at}>"
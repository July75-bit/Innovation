"""选手（虚拟资产标的）。

字段与 docs/software/database_design.md §2.2 一致。

数据口径：
- name / display_name / team / role 为真实公开信息；
- current_price / prev_price 与 rating（0–100 模拟综合表现分）为本项目模拟数据，
  不是 HLTV Rating，也不代表真实身价，UI 必须标注"模拟"；
- initial_price 不是本表字段，落库为 price_history 的第一条（reason = 初始价格）。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.position import Position
    from app.models.price_history import PriceHistory
    from app.models.trade import Trade


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        CheckConstraint("current_price > 0", name="ck_players_current_price_positive"),
        CheckConstraint("prev_price > 0", name="ck_players_prev_price_positive"),
        CheckConstraint("rating >= 0 AND rating <= 100", name="ck_players_rating_range"),
    )

    player_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    team: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    prev_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # 0–100 的项目模拟综合表现分（C 维护），非官方统计
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="trading", server_default="trading"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
    positions: Mapped[list["Position"]] = relationship(back_populates="player")
    trades: Mapped[list["Trade"]] = relationship(back_populates="player")

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<Player player_id={self.player_id} name={self.name!r} price={self.current_price}>"

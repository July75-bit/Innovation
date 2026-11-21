"""价格历史（只追加）。

字段与 docs/software/database_design.md §2.5 一致：
price_id / player_id / price / reason / ts。

契约要求（api_contract.md §4.4）：
- 按 ts 升序返回，供前端折线图直接使用；
- 每条必须带 reason（涨跌归因，答辩要拆解）；
- 空历史返回空数组，不返回 404。

写入方（第 3 天定死，见 `docs/software/database_design.md` §3.2）：C 只算 `PriceUpdate`，
**B 负责落库**——`app/core/price_update.py` 与 `scripts/update_prices.py`；
种子脚本也写首条（reason = 初始价格）。B 的交易接口只读改价后的结果，绝不改价。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow

if TYPE_CHECKING:
    from app.models.player import Player


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_player_ts", "player_id", "ts"),
        CheckConstraint("price > 0", name="ck_price_history_price_positive"),
    )

    price_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # 人类可读的涨跌原因，必填
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    player: Mapped["Player"] = relationship(back_populates="price_history")

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return (
            f"<PriceHistory price_id={self.price_id} player_id={self.player_id} "
            f"price={self.price} reason={self.reason!r}>"
        )

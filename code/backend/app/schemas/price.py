"""价格历史响应模型（契约 §4.4）。

结构固定为 {player_id, points: [...]}，points 按 ts 升序；空历史返回 points: []。
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import UtcDateTime


class PricePoint(BaseModel):
    ts: UtcDateTime
    price: float
    reason: str


class PriceHistoryResponse(BaseModel):
    player_id: int
    points: list[PricePoint]

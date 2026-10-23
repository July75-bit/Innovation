"""交易请求 / 响应模型（契约 §4.7 / §4.8 / §4.9）。

买入请求 ``{"player_id": 1, "quantity": 2}``：
- ``player_id`` 必须存在（否则 404，由接口层判断）；
- ``quantity`` 必须是正整数，这里用 Field(ge=1) 拦住 0 / 负数，
  非整数（小数、字符串）也由 Pydantic 拒绝 → 422 VALIDATION_ERROR。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import UtcDateTime


class TradeRequest(BaseModel):
    player_id: int = Field(gt=0, description="选手 ID（不是 id）")
    # strict=True：只接受 JSON 整数，"2" / 1.5 / true 都算非法（契约要求正整数）
    quantity: int = Field(ge=1, strict=True, description="交易数量，必须是正整数")


class TradeResponse(BaseModel):
    success: bool = True
    message: str
    balance: float
    player_id: int
    quantity: int
    price: float
    trade_id: int


class TradeItem(BaseModel):
    trade_id: int
    player_id: int
    name: str
    side: str
    quantity: int
    price: float
    amount: float
    balance_after: float
    created_at: UtcDateTime

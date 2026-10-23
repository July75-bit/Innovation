"""账户响应模型（契约 §4.5）。"""

from __future__ import annotations

from pydantic import BaseModel


class AccountResponse(BaseModel):
    user_id: int
    balance: float
    initial_balance: float
    # 持仓当前市值合计
    position_value: float
    # balance + position_value
    total_asset: float

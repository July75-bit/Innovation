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


class AccountRebuildResponse(BaseModel):
    """余额重建结果（POST /api/account/rebuild）：只影响当前账户。"""

    user_id: int
    balance: float
    cleared_positions: int
    cleared_trades: int
    note: str

"""账户响应模型（契约 §4.5）。"""

from __future__ import annotations

from datetime import datetime

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


class AssetPoint(BaseModel):
    """某一时刻的资产快照：现金 + 持仓市值 = 总资产。"""

    ts: datetime
    cash: float
    position_value: float
    total_asset: float


class AccountStats(BaseModel):
    """个人页统计卡（全部来自当前账户，不含他人数据）。"""

    trades: int
    buys: int
    sells: int
    buy_amount: float
    sell_amount: float
    positions: int
    position_value: float
    profit: float


class AccountHistoryResponse(BaseModel):
    """资产曲线 + 统计（GET /api/account/history）。"""

    initial_balance: float
    points: list[AssetPoint]
    stats: AccountStats

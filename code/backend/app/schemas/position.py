"""持仓响应模型（契约 §4.6）。"""

from __future__ import annotations

from pydantic import BaseModel


class PositionItem(BaseModel):
    player_id: int
    name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    profit: float
    profit_pct: float

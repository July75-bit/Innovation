"""选手市场响应模型（契约 §4.2 / §4.3）。"""

from __future__ import annotations

from pydantic import BaseModel


class PlayerSummary(BaseModel):
    player_id: int
    name: str
    display_name: str | None = None
    team: str | None = None
    role: str | None = None
    current_price: float
    prev_price: float
    change_pct: float
    # 0–100 的项目模拟综合表现分，UI 必须标注"模拟"
    rating: int
    status: str


class PlayerDetail(PlayerSummary):
    # 最近一次价格变化原因（来自 price_history.reason），无历史时为 None
    latest_reason: str | None = None

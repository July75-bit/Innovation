"""Pydantic 请求 / 响应模型统一导出。

命名与 docs/software/api_contract.md 对齐，字段名一旦发布即视为契约：

- PlayerSummary      市场列表项（player_id 不叫 id；current_price / prev_price / change_pct）
- PlayerDetail       PlayerSummary + latest_reason
- AccountResponse    user_id / balance / initial_balance / position_value / total_asset
- PositionItem       player_id / name / quantity / avg_cost / current_price / market_value / profit / profit_pct
- PricePoint         时间升序用的单点（ts / price / reason）
- PriceHistoryResponse  {player_id, points: [...]}
- TradeRequest       {player_id, quantity}，quantity 在这里就要求正整数
- TradeResponse      买入/卖出成功结构
- TradeItem          流水列表项（side = BUY / SELL）

约定：金额统一 float（两位小数），时间统一 ISO 8601 UTC 字符串（以 Z 结尾）。
"""

from app.schemas.account import AccountResponse
from app.schemas.common import UtcDateTime
from app.schemas.player import PlayerDetail, PlayerSummary
from app.schemas.position import PositionItem
from app.schemas.price import PriceHistoryResponse, PricePoint
from app.schemas.trade import TradeItem, TradeRequest, TradeResponse

__all__ = [
    "AccountResponse",
    "PlayerDetail",
    "PlayerSummary",
    "PositionItem",
    "PriceHistoryResponse",
    "PricePoint",
    "TradeItem",
    "TradeRequest",
    "TradeResponse",
    "UtcDateTime",
]

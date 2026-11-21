"""SQLAlchemy 模型统一导出。

九张表与 docs/software/database_design.md 一一对应：

| 模型 | 表 | 说明 |
| --- | --- | --- |
| User | users | 虚拟账户（初始 5000 信用点） |
| Player | players | 选手（虚拟资产标的，价格/评分为模拟数据） |
| Position | positions | 持仓（UNIQUE(user_id, player_id)） |
| Trade | trades | 交易流水（只追加，INDEX(user_id, created_at)） |
| PriceHistory | price_history | 价格历史（INDEX(player_id, ts)，reason 必填） |
| AuthToken | auth_tokens | 访问令牌（只存 SHA-256，第 7 轮私人账号） |
| AgentTrace | agent_traces | 智能体调用审计（模式/来源/耗时/降级原因） |
| DecisionLog | decision_logs | 人在环：采纳/忽略建议的记录 |
| PriceNarrative | price_narratives | 价格变动的叙事归因缓存 |

新增表务必在这里登记，``init_db()`` 依赖本文件的导入注册元数据。
"""

from app.models.agent import AgentTrace, DecisionLog, PriceNarrative
from app.models.auth_token import AuthToken
from app.models.price_history import PriceHistory
from app.models.player import Player
from app.models.position import Position
from app.models.trade import Trade
from app.models.user import User

__all__ = [
    "User",
    "Player",
    "Position",
    "Trade",
    "PriceHistory",
    "AuthToken",
    "AgentTrace",
    "DecisionLog",
    "PriceNarrative",
]

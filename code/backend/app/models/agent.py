"""智能体审计与人在环记录（第 8 轮：强化智能体占比）。

三张表分工（都不碰业务表，交易/定价零影响）：

| 模型 | 表 | 作用 |
| --- | --- | --- |
| AgentTrace | agent_traces | 每次智能体调用的**审计行**：模式/来源/耗时/降级原因/输出快照 |
| DecisionLog | decision_logs | **人在环**：用户采纳/忽略某条建议的记录（含建议与实际动作） |
| PriceNarrative | price_narratives | 价格变动的**叙事归因**缓存（LLM 生成、按 (player_id, ts) 唯一） |

为什么单独建表而不复用日志文件：答辩要能"查得到、统计得出"——
`GET /api/agent/traces` 与 `GET /api/agent/decisions/stats` 直接读这三张表，
不依赖文件系统（Render 免费实例文件系统是临时的）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class AgentTrace(Base):
    """一次智能体调用的审计记录（只追加，不改不删）。"""

    __tablename__ = "agent_traces"

    trace_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    # single = 单次分析；decision = 决策卡；panel = 多角色协作；brief = 今日简报；narrative = 归因叙事
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.player_id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)  # llm / rule_fallback
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 降级原因（无密钥/超时/脏输出…），正常调用为 NULL
    fallback_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 输入摘要（不存原文，避免把账户数据留底）与输出快照
    input_digest: Mapped[str | None] = mapped_column(String(120), nullable=True)
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DecisionLog(Base):
    """人在环：用户对某条建议的采纳/忽略。"""

    __tablename__ = "decision_logs"

    decision_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False
    )
    advice_action: Mapped[str] = mapped_column(String(8), nullable=False)  # BUY/SELL/HOLD
    advice_source: Mapped[str] = mapped_column(String(16), nullable=False)
    # accept = 采纳了建议；ignore = 看了但不采纳
    decision: Mapped[str] = mapped_column(String(8), nullable=False)
    trace_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)


class PriceNarrative(Base):
    """价格变动的叙事归因（LLM 生成，按 (player_id, ts) 缓存一次）。"""

    __tablename__ = "price_narratives"
    __table_args__ = (UniqueConstraint("player_id", "ts", name="uq_narrative_player_ts"),)

    narrative_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False, index=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)  # llm / rule_fallback
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

"""SQLAlchemy 模型。

负责人：B

按 B 的 D1 计划，需要设计 5 张表（表名与字段确定后同步到
docs/software/database_design.md，并@A @C 确认字段名）：

- users        账户：id, nickname, balance, initial_balance, created_at
- players      选手：id, name, display_name, team, role, current_price, prev_price,
                rating, hltv_rating, kast, adr, status, updated_at
- positions    持仓：id, user_id, player_id, quantity, avg_cost, updated_at
                （user_id + player_id 唯一索引）
- trades       交易记录：id, user_id, player_id, side(BUY/SELL), quantity, price,
                amount, balance_after, created_at
- price_history 价格历史：id, player_id, price, reason, ts
                （player_id + ts 索引，供折线图和 AI 分析取数）

写模型时的注意事项：
1. 金额用 Numeric/Float 要统一，别一半 int 一半 float；
2. created_at/ts 统一时区策略，前端 `new Date()` 要能解析；
3. 持仓上限、初始资金等数值从 app.core.config.settings 取，不要写死。

示例（B 取消注释并补全即可）：

    from datetime import datetime
    from sqlalchemy import Float, ForeignKey, Integer, String, DateTime, UniqueConstraint
    from sqlalchemy.orm import Mapped, mapped_column
    from app.core.database import Base

    class Player(Base):
        __tablename__ = "players"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(50), nullable=False)
        ...
"""

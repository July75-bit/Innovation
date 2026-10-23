"""接口公共依赖。

第 1 天不做登录（契约与分工都允许"演示账户"）：所有请求默认作用于
nickname = "demo" 的账户，余额不足时自动按 settings.initial_balance 创建。

第 2 天接入登录后，只需把 get_current_user 改成从 token 解析 user_id，
其余接口不用动。
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import User

DEMO_NICKNAME = "demo"


def get_current_user(db: Session = Depends(get_db)) -> User:
    """取演示账户；不存在则按初始 5000 虚拟币创建。"""
    user = db.scalar(select(User).where(User.nickname == DEMO_NICKNAME))
    if user is None:
        initial = Decimal(settings.initial_balance)
        user = User(nickname=DEMO_NICKNAME, balance=initial, initial_balance=initial)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

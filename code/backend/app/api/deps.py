"""接口公共依赖。

负责人：B（第 7 轮补上私人账号解析）

当前用户怎么定（契约 §4.11）：

| 请求头 | 落到哪个账户 |
| --- | --- |
| `Authorization: Bearer <有效令牌>` | 该令牌对应的**私人账户** |
| `Authorization` 带了但令牌无效/过期 | **401 UNAUTHORIZED**（不静默降级，否则"退出后还以为自己登录着"） |
| 完全没带 `Authorization` | **公共演示账户 `demo`**：未登录访客，也是第 1~6 轮所有测试与脚本走的兼容路径 |

第 1 天的注释里写"接上登录后只需把 get_current_user 改成从 token 解析 user_id"，
第 7 轮真的接上了：改动只在这一个函数里，其余接口靠 `Depends(get_current_user)` 自动分账。
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.security import TOKEN_TTL, hash_token, new_token
from app.core.time import utcnow
from app.models import AuthToken, User

#: 公共演示账户的用户名。历史数据都挂在它身上，第 7 轮起作为"未登录访客"的兜底账户
DEMO_NICKNAME = "demo"


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite 不存时区，读出来是 naive；统一按 UTC 解释后才能安全比较。"""
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def bearer_token(authorization: str | None) -> str | None:
    """从 `Authorization: Bearer xxx` 取令牌原文；没带头返回 None。

    带了头但格式不对 → 401：这种情况多半是前端拼错了头，静默当访客更难排查。

    开头那个 isinstance 判断不是防御性摆设：`tests/unit/test_infra_guards.py` 会**直接调用**
    `get_current_user(db)` 而不走 FastAPI 的依赖注入，此时参数默认值是 `Header(...)` 这个
    FieldInfo 对象而不是 None——不挡住就会在 `.strip()` 上炸成
    `AttributeError: 'Header' object has no attribute 'strip'`（第 7 轮合并时实测踩过）。
    """
    if not isinstance(authorization, str):
        return None
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ApiError(
            "认证头格式不对：需要 Authorization: Bearer <令牌>",
            status_code=401,
            code="UNAUTHORIZED",
        )
    return parts[1].strip()


def get_public_demo_user(db: Session) -> User:
    """取公共演示账户；不存在则按初始 5000 虚拟币创建（第 1 天原逻辑）。"""
    user = db.scalar(select(User).where(User.nickname == DEMO_NICKNAME))
    if user is None:
        initial = Decimal(settings.initial_balance)
        user = User(nickname=DEMO_NICKNAME, balance=initial, initial_balance=initial)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User:
    """当前用户：有令牌认私人账户，没令牌用公共演示账户。

    参数必须写成 `Annotated[str | None, Header(...)] = None`，不能写成 `= Header(default=None)`：
    后者在函数被**直接调用**（守卫测试就是这么调的）时，默认值是一个 FieldInfo 对象而不是 None。
    """
    raw = bearer_token(authorization)
    if raw is None:
        return get_public_demo_user(db)

    row = db.get(AuthToken, hash_token(raw))
    expires_at = _as_utc(row.expires_at) if row is not None else None
    if row is None or (expires_at is not None and expires_at < utcnow()):
        raise ApiError("登录状态已失效，请重新登录", status_code=401, code="UNAUTHORIZED")

    user = db.get(User, row.user_id)
    if user is None:
        # 用户被删了但令牌行还在：按失效处理，别让一个 500 挡住整页
        raise ApiError("登录状态已失效，请重新登录", status_code=401, code="UNAUTHORIZED")
    return user


def issue_token(db: Session, user: User) -> tuple[str, datetime]:
    """发一枚不透明令牌（原文只在这一次返回里出现，库里只存 SHA-256）。"""
    raw, token_hash = new_token()
    expires_at = utcnow() + TOKEN_TTL
    db.add(
        AuthToken(
            token_hash=token_hash,
            user_id=user.user_id,
            created_at=utcnow(),
            expires_at=expires_at,
        )
    )
    return raw, expires_at


def revoke_token(db: Session, authorization: str | None) -> bool:
    """撤销当前令牌（退出登录）。返回是否真的删掉了一行。"""
    raw = bearer_token(authorization)
    if raw is None:
        return False
    row = db.get(AuthToken, hash_token(raw))
    if row is None:
        return False
    db.delete(row)
    return True
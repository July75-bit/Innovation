"""注册 / 登录 / 退出 / 当前身份。

负责人：B（路由与事务）+ A（前端 useAuth 接线）

设计要点：
1. **口令只在后端散列**（PBKDF2-HMAC-SHA256，见 app/core/security.py），
   前端永远拿不到散列，后端也不存明文；
2. **令牌不透明**：原文给客户端一次，库里只存 SHA-256，撤销即失效（不是前端删存储的假退出）；
3. **公共演示账户 demo 保留**：未登录（不带 Authorization）时所有人共用它，历史数据不迁走；
   注册出来的新账号有自己独立的一行 balance / positions / trades；
4. `demo` 这个用户名被保留：否则有人注册 demo 后以为自己"接管"了公共账户。

错误全部走 app/core/errors.py 的统一 JSON（契约 §2），message 可直接展示给同学看。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import DEMO_NICKNAME, bearer_token, get_current_user, issue_token, revoke_token
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.security import hash_password, validate_password, validate_username, verify_password
from app.core.time import utcnow
from app.models import AuthToken, Position, Trade, User
from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    DeleteAccountRequest,
    DeleteAccountResponse,
    LoginRequest,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
)

logger = logging.getLogger("playerstock.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        user_id=user.user_id,
        nickname=user.nickname,
        balance=float(Decimal(user.balance)),
        initial_balance=float(Decimal(user.initial_balance)),
        created_at=user.created_at,
        account_type="public_demo" if user.password_hash is None else "private",
    )


def _find_by_name(db: Session, name: str) -> User | None:
    """用户名查找：大小写不敏感（`ZywOo` 与 `zywoo` 视为同一个账号名）。"""
    return db.scalar(select(User).where(func.lower(User.nickname) == name.lower()))


@router.post("/register", response_model=AuthResponse, summary="注册私人账号", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """注册即登录：成功直接返回令牌，前端不用再发一次登录请求。"""
    name = body.username.strip()
    invalid = validate_username(name) or validate_password(body.password)
    if invalid:
        raise ApiError(invalid, status_code=422, code="INVALID_INPUT")
    if name.lower() == DEMO_NICKNAME:
        raise ApiError(
            f"用户名 {DEMO_NICKNAME} 是公共演示账户，换一个名字",
            status_code=409,
            code="USERNAME_RESERVED",
        )
    if _find_by_name(db, name) is not None:
        raise ApiError(f"用户名 {name} 已被注册", status_code=409, code="USERNAME_TAKEN")

    salt, password_hash = hash_password(body.password)
    initial = Decimal(settings.initial_balance)
    user = User(
        nickname=name,
        balance=initial,
        initial_balance=initial,
        salt=salt,
        password_hash=password_hash,
    )
    db.add(user)
    try:
        db.flush()  # 拿到 user_id
    except IntegrityError as exc:
        # 并发注册同名：靠 users.nickname 的 UNIQUE 兜底，转成人话而不是 500
        db.rollback()
        raise ApiError(f"用户名 {name} 已被注册", status_code=409, code="USERNAME_TAKEN") from exc

    token, expires_at = issue_token(db, user)
    db.commit()
    return AuthResponse(token=token, expires_at=expires_at, user=_to_auth_user(user))


@router.post("/login", response_model=AuthResponse, summary="登录")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    name = body.username.strip()
    user = _find_by_name(db, name)
    # 用户名不存在与密码错都是同一句提示 + 同一个 401：
    # 本地演示可以分开提示，但这里已经是真后端接口，不该用来枚举账号名
    if user is None or not verify_password(body.password, user.salt, user.password_hash):
        raise ApiError("用户名或密码不正确", status_code=401, code="INVALID_CREDENTIALS")
    if user.password_hash is None:
        raise ApiError(
            "公共演示账户不支持密码登录，请直接访问（未登录即为公共账户）",
            status_code=403,
            code="PUBLIC_ACCOUNT",
        )

    token, expires_at = issue_token(db, user)
    _purge_expired(db, user.user_id)
    db.commit()
    return AuthResponse(token=token, expires_at=expires_at, user=_to_auth_user(user))


@router.get("/me", response_model=MeResponse, summary="当前身份")
def me(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> MeResponse:
    """前端启动时用它校验本地存的令牌还管不管用（无效会被 get_current_user 打成 401）。"""
    return MeResponse(
        authenticated=bearer_token(authorization) is not None,
        user=_to_auth_user(user),
    )


@router.post("/logout", response_model=LogoutResponse, summary="退出登录")
def logout(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> LogoutResponse:
    """撤销当前令牌。没带令牌也返回成功（幂等：前端清本地存储后重复调用不该报错）。"""
    revoked = revoke_token(db, authorization)
    db.commit()
    return LogoutResponse(message="已退出登录", revoked=revoked)


@router.delete(
    "/account",
    response_model=DeleteAccountResponse,
    summary="删除账号（含持仓与流水，不可恢复）",
)
def delete_account(
    body: DeleteAccountRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> DeleteAccountResponse:
    """删除**当前令牌所属的私人账号**，级联清掉它的持仓 / 流水 / 令牌。

    四道闸，少一道都可能删错东西：
    1. 必须带令牌：没带 Authorization 时 get_current_user 会给出公共演示账户，
       而公共账户不属于任何个人，删它等于删大家的演示数据 → 401；
    2. 必须是私人账户（有口令）：`demo` 一律 403 `PUBLIC_ACCOUNT`；
    3. 必须再输一次口令：只靠令牌就能删号，在共用电脑上是不可接受的失败模式；
    4. 统计并返回删掉的行数：让"级联删干净了"这件事在响应里可见，而不是靠承诺。

    删除顺序按外键来（positions / trades / auth_tokens → users），
    这样即使某个环境的 SQLite 没开 `PRAGMA foreign_keys`，也不会留下孤儿行。
    """
    if bearer_token(authorization) is None:
        raise ApiError(
            "公共演示账户不能删除：请先登录自己的账号",
            status_code=401,
            code="UNAUTHORIZED",
        )
    if user.password_hash is None:
        raise ApiError(
            f"账户 {user.nickname} 是公共演示账户，不支持删除",
            status_code=403,
            code="PUBLIC_ACCOUNT",
        )
    if not verify_password(body.password, user.salt, user.password_hash):
        raise ApiError("密码不正确，未能删除账号", status_code=401, code="INVALID_CREDENTIALS")

    deleted_positions = db.scalar(
        select(func.count()).select_from(Position).where(Position.user_id == user.user_id)
    )
    deleted_trades = db.scalar(
        select(func.count()).select_from(Trade).where(Trade.user_id == user.user_id)
    )
    tokens = db.scalars(select(AuthToken).where(AuthToken.user_id == user.user_id)).all()
    deleted_tokens = len(tokens)

    # 先删子表再删 users：bulk DELETE 一条语句清干净，不依赖 ORM 级联，
    # 也就不怕某个环境的 SQLite 忘了开 PRAGMA foreign_keys（开没开结果都一样）
    for row in tokens:
        db.delete(row)
    db.execute(delete(Position).where(Position.user_id == user.user_id))
    db.execute(delete(Trade).where(Trade.user_id == user.user_id))
    db.delete(user)
    db.commit()

    logger.info(
        "账号已删除：user_id=%s nickname=%s 持仓 %s 条 / 流水 %s 条 / 令牌 %s 条",
        user.user_id,
        user.nickname,
        deleted_positions,
        deleted_trades,
        deleted_tokens,
    )
    return DeleteAccountResponse(
        message="账号已删除",
        deleted_positions=int(deleted_positions or 0),
        deleted_trades=int(deleted_trades or 0),
        deleted_tokens=deleted_tokens,
    )


def _purge_expired(db: Session, user_id: int) -> int:
    """登录时顺手清掉该用户已过期的令牌，免得 auth_tokens 只增不减。

    SQLite 读出来是 naive datetime，所以把过期判断下推到 Python：
    表很小（一人几条），比写一段跨方言的 SQL 比较更省事也不容易错。
    """
    now = utcnow()
    rows = db.scalars(select(AuthToken).where(AuthToken.user_id == user_id)).all()
    stale = [row for row in rows if _aware(row.expires_at) < now]
    for row in stale:
        db.delete(row)
    return len(stale)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


__all__ = ["router"]
"""注册 / 登录的请求与响应模型（契约 §4.11~§4.14）。

字段一律 snake_case，与其余接口一致（契约 §5）。
`account_type` 是给前端标注身份用的：private = 私人账户，public_demo = 公共演示账户。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import UtcDateTime


class RegisterRequest(BaseModel):
    """字段规则**只在这里设上限**，具体格式交给 app/core/security.py 校验。

    为什么不用 Pydantic 的 min_length/pattern：那样"用户名太短"会走 422 VALIDATION_ERROR、
    "密码没数字"走 422 INVALID_INPUT，同一类问题两个错误码，前端得写两套分支。
    统一在接口层校验 → 一个错误码、一句能直接展示的中文（契约 §2）。
    上限仍然必要：PBKDF2 的耗时随口令长度线性增长，得挡住超长输入。
    """

    username: str = Field(max_length=50)
    password: str = Field(max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class AuthUser(BaseModel):
    user_id: int
    nickname: str
    balance: float
    initial_balance: float
    created_at: UtcDateTime
    account_type: str


class AuthResponse(BaseModel):
    """注册 / 登录成功：返回令牌原文（此后请求带在 Authorization 头里）与账户信息。"""

    token: str
    expires_at: UtcDateTime
    user: AuthUser


class MeResponse(BaseModel):
    """`GET /api/auth/me`：只回身份，不回令牌。"""

    authenticated: bool
    user: AuthUser


class LogoutResponse(BaseModel):
    success: bool = True
    message: str
    revoked: bool = False


class DeleteAccountRequest(BaseModel):
    """删除账号必须再输一次口令。

    为什么不做成"点一下就走"：删的是余额 / 持仓 / 流水，**不可恢复**。
    令牌泄露（共用电脑忘了退出）时，只靠令牌就能删号是不可接受的失败模式。
    """

    password: str = Field(max_length=128)


class DeleteAccountResponse(BaseModel):
    success: bool = True
    message: str
    # 顺手告诉前端删掉了多少条数据，答辩时"级联删干净了"有地方可指
    deleted_positions: int
    deleted_trades: int
    deleted_tokens: int
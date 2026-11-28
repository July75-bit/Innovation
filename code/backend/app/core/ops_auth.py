"""运维接口口令校验（重灌 `/api/debug/reseed`、赛后结算 `/api/prices/recalc` 共用）。

负责人：B（D 于 2026-11-26 代做，原因见下）

为什么要有：这两个接口都能改线上行情。以前 recalc 完全不校验，任何人换个比赛日期
就能把某名选手连拉 +15%；reseed 的默认口令又写在公开仓库里。规则收紧为：

1. `RESEED_TOKEN` 没配置 → 运维接口一律 403 `OPS_TOKEN_UNSET`（宁可用不了，也不默认放开）；
2. 部署在 Render 上却还用 `.env.example` 里那个公开示例值 → 视同没配置；
3. 口令不匹配 → 403 `TOKEN_MISMATCH`，用 `hmac.compare_digest` 做常量时间比较。
"""

from __future__ import annotations

import hmac
import os

from app.core.config import settings
from app.core.errors import ApiError

#: `.env.example` 里的示例口令：只适合本机开发，线上用它等于没设
PUBLIC_EXAMPLE_TOKEN = "playerstock-demo-reseed-2026"


def configured_ops_token() -> str:
    """返回生效的运维口令；空串表示运维接口已禁用。"""
    token = (settings.reseed_token or "").strip()
    if os.getenv("RENDER") and token == PUBLIC_EXAMPLE_TOKEN:
        return ""
    return token


def require_ops_token(token: str | None) -> None:
    expected = configured_ops_token()
    if not expected:
        raise ApiError(
            "运维接口未启用：请在部署平台设置随机的 RESEED_TOKEN",
            status_code=403,
            code="OPS_TOKEN_UNSET",
        )
    if not token or not hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
        raise ApiError("运维口令不匹配", status_code=403, code="TOKEN_MISMATCH")

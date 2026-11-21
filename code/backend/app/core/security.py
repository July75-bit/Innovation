"""口令散列与访问令牌（第 7 轮：私人账号）。

为什么自己实现、不引第三方库：
- 依赖是封闭锁定的（`requirements.lock.txt` 满足课程"可复现"硬要求），
  加 passlib / python-jose 之类要重新生成锁文件并动 CI，收益却只是省二十行；
- 需求只有"注册 / 登录 + 可撤销的不透明令牌"，标准库 `hashlib.pbkdf2_hmac` +
  `secrets` 就够，PBKDF2-HMAC-SHA256 本身是 NIST SP 800-132 认可的口令派生函数。

存法：`pbkdf2_sha256$<迭代次数>$<盐 hex>$<散列 hex>`，盐每用户独立随机。
验证用 `hmac.compare_digest`（常量时间比较），不给计时侧信道留口子。

令牌：`secrets.token_urlsafe(32)` 原文只回给客户端一次，**库里只存它的 SHA-256**——
即使拖库也拿不到能用的令牌；撤销 = 删行，所以退出登录是真的失效，不是前端删 localStorage。
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import timedelta

ALGORITHM = "pbkdf2_sha256"
# 本地实测约 40ms/次：人眼无感（注册/登录本来就是一次性动作），爆破方要付 25 倍代价
PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16
TOKEN_BYTES = 32
TOKEN_TTL = timedelta(days=30)

# 与前端 src/composables/useAuth.ts 的规则保持一致：两边都校验，谁也不能绕过谁
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def validate_username(name: str) -> str | None:
    """返回中文错误信息；None 表示合法（message 可直接给用户看，契约 §2）。"""
    if not name:
        return "请填写用户名"
    if len(name) < 3:
        return "用户名至少 3 个字符"
    if len(name) > 20:
        return "用户名最多 20 个字符"
    if not USERNAME_PATTERN.match(name):
        return "用户名只能用字母、数字和下划线"
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "请填写密码"
    if len(password) < 8:
        return "密码至少 8 位"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "密码需同时包含字母和数字"
    return None


def hash_password(password: str) -> tuple[str, str]:
    """返回 (salt_hex, 可入库的 password_hash)。"""
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return salt, f"{ALGORITHM}${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, salt: str | None, stored: str | None) -> bool:
    """校验口令。公共演示账户没有口令字段，这里一律返回 False（不许用密码"猜"进公共账户）。"""
    if not stored or "$" not in stored:
        return False
    try:
        algorithm, iterations, stored_salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM or not stored_salt or stored_salt != (salt or stored_salt):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(stored_salt), int(iterations)
    )
    return hmac.compare_digest(digest.hex(), expected)


def new_token() -> tuple[str, str]:
    """返回 (发给客户端的原文, 入库的 SHA-256 hex)。"""
    raw = secrets.token_urlsafe(TOKEN_BYTES)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
"""时间工具：全站统一 ISO 8601 UTC。

契约（docs/software/api_contract.md §1）：时间统一 UTC，形如
``2026-01-01T10:05:00Z``，前端 ``new Date()`` 可直接解析。
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """带时区的当前 UTC 时间，写库用。"""
    return datetime.now(timezone.utc)


def to_utc_iso(value: datetime | None) -> str | None:
    """把库里的时间统一序列化成以 ``Z`` 结尾的 UTC 字符串。

    SQLite 不保存时区，读出来的 naive datetime 统一按 UTC 解释。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

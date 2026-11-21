"""Pydantic 通用类型。"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import PlainSerializer

from app.core.time import to_utc_iso

# 统一输出 ISO 8601 UTC（2026-01-01T10:05:00Z），前端 new Date() 可直接解析
UtcDateTime = Annotated[datetime, PlainSerializer(to_utc_iso, return_type=str)]

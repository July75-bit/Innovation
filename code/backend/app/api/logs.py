"""运行日志自检接口（D，2026-11-07）。

**用途**：线上（Render）没有终端，出问题时打开一个网址就能看最近日志——

    GET /api/debug/logs?lines=100
    GET /api/debug/logs?lines=200&level=WARNING

**与 `debug.py` 同一套开关**：`DEBUG_ENDPOINTS=0` 时本接口也返回 404，
**只读**、不接受任何文件路径输入（路径来自服务端配置），因此没有目录穿越面。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.errors import ApiError
from app.core.logging_config import current_log_path, recent_lines

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/logs", summary="只读：最近的运行日志（默认 100 行）")
def debug_logs(
    lines: int = Query(100, ge=1, le=500, description="返回最后多少行"),
    level: str | None = Query(
        None, description="只看某个级别：WARNING / ERROR / INFO（留空返回全部）"
    ),
) -> dict:
    """返回日志文件末尾若干行，供线上排查与答辩演示"出错能自查"。"""
    if not settings.debug_endpoints:
        raise ApiError(
            "调试接口已关闭（DEBUG_ENDPOINTS=0）",
            status_code=404,
            code="ENDPOINT_DISABLED",
        )

    path = current_log_path()
    rows = recent_lines(lines)

    if level:
        wanted = level.strip().upper()
        rows = [row for row in rows if f" {wanted}" in row]

    return {
        "日志文件": str(path) if path else "（尚未初始化：日志在应用启动时创建）",
        "返回行数": len(rows),
        "过滤级别": level.upper() if level else "全部",
        "内容": rows,
        "提示": "只读；不含口令/token/连接串。可用 DEBUG_ENDPOINTS=0 关闭本接口。",
    }

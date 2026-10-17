"""健康检查 —— 已实现，可直接用于第 1 天的"前端连上后端"验收。

负责人：B
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "playerstock-backend"}

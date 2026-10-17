"""FastAPI 应用入口。

负责人：B

启动（在 backend/ 目录下）：
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

验收：
    GET /              -> 项目信息
    GET /api/health    -> {"status": "ok", "service": "playerstock-backend"}
    GET /docs          -> Swagger 交互式文档
"""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account, ai, health, players, positions, prices, trades
from app.core.config import settings
from app.core.database import init_db

logger = logging.getLogger("playerstock")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 线上必须用托管 Postgres；这里在 Render 上检测到 SQLite 就大声警告，
    # 避免"数据总是丢"却查不出原因（免费实例的文件系统是临时的）。
    if settings.is_sqlite and os.getenv("RENDER"):
        logger.warning(
            "当前部署在 Render 上却使用本地 SQLite：重新部署/重启/休眠后数据会全部丢失！"
            "请把 DATABASE_URL 设为 Render Postgres 的连接串（scheme 用 postgresql://）。"
        )
    # 开发期直接建表；表结构由 B 在 app/models/ 中定义
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="虚拟选手股交易与智能体市场模拟系统（虚拟币，不可兑换）",
    version=settings.app_version,
    lifespan=lifespan,
)

# A 的前端在 5173；线上换成静态站点域名，通过 CORS_ORIGINS 环境变量控制
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"], summary="项目信息")
def root() -> dict[str, str]:
    return {
        "project": "PlayerStock",
        "message": "PlayerStock API is running",
        "version": settings.app_version,
        "docs": "/docs",
    }


# 统一挂到 /api 前缀下，对应 docs/software/api_contract.md 里的路径
for _module in (health, players, account, trades, positions, prices, ai):
    app.include_router(_module.router, prefix=settings.api_prefix)

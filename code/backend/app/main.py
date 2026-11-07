"""FastAPI 应用入口。

负责人：B

启动（在 code/backend/ 目录下）：
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

from app.api import account, ai, debug, health, players, positions, prices, trades
from app.core.config import settings
from app.core.database import init_db
from app.core.errors import register_exception_handlers

logger = logging.getLogger("playerstock")

#: 本地开发默认放行的来源（与 `config.cors_origins` 的默认值一致）
DEV_ORIGINS = frozenset({"http://localhost:5173", "http://127.0.0.1:5173"})


def resolve_cors_origins() -> list[str]:
    """决定 CORS 放行哪些来源（第 5 天 B 的决策，落文档见 `deployment.md` §6 / `compliance.md` §4）。

    依据 `docs/requirements/nonfunctional_spec.md` 的 **NFR-S-04**：
    "部署后仅开放必要 CORS 来源，不使用 `allow_origins=["*"]`"。

    规则（按优先级）：
    1. `CORS_ORIGINS` 配了具体域名 → **按白名单放行**（默认路径，合规要求）；
    2. `CORS_ORIGINS` 显式写 `*` → 放行全部，但启动日志会写明"当前放开全部来源"；
    3. `CORS_ORIGINS` 为空 → 退化为 `*` 并 **WARNING**；
    4. **线上（Render）但配置仍是本地默认值** → 视为"忘配了"，同样退化并 WARNING。

    第 4 条是 2026-10-25 线上事故补的：当时后端已换成配置驱动、但 Render 上的
    `CORS_ORIGINS` 没填，于是按 `config.py` 的默认值只放行 `localhost:5173`，
    结果**线上前端被跨域拦掉**（`access-control-allow-origin` 直接没有）。
    只判断"空列表"覆盖不到这种真实误配，所以把"线上却还是本地默认值"也算未配置。

    为什么不直接硬编码 `*`：`*` 会让"配置漏填"变成无声事故——前端能连、也连得上
    任何来源，日志里看不出问题；反过来只认白名单又会让"忘了填环境变量"直接白屏。
    所以做成"**默认白名单、缺配置时退化并告警**"，两种事故都能在日志里被看见。
    """
    origins = settings.cors_origin_list
    if not origins:
        logger.warning(
            "CORS_ORIGINS 未配置：临时放开全部来源（演示兜底）。"
            "请在部署平台把 CORS_ORIGINS 设为前端公网地址（见 deployment.md §2）。"
        )
        return ["*"]
    if "*" in origins:
        logger.warning("CORS_ORIGINS 显式包含 *：放行全部来源（已记录，便于答辩时说明）。")
        return ["*"]
    if os.getenv("RENDER") and set(origins) <= DEV_ORIGINS:
        logger.warning(
            "线上检测到 CORS_ORIGINS 仍是本地默认值（%s）：退化为放开全部来源。"
            "请把 CORS_ORIGINS 设为前端公网地址（如 https://playerstock-frontend-mdlk.onrender.com）。",
            ", ".join(origins),
        )
        return ["*"]
    return origins


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 把"当前用什么库、放行哪些来源"打到启动日志里：
    # ① 线上排查"数据为什么丢"时第一眼就能看到是不是误用了 SQLite；
    # ② 这两行也是第 5 天检查单里"后端日志"截图要拍的内容。
    logger.info(
        "数据库：%s",
        "SQLite（本地/演示，重启不保证持久）" if settings.is_sqlite else "Postgres（持久化生效）",
    )
    logger.info("CORS 放行来源：%s", ", ".join(resolve_cors_origins()))
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
    allow_origins=resolve_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 统一错误格式：所有 4xx/5xx 都是 {"success": false, "message": 中文, "code": ...}
register_exception_handlers(app)


@app.get("/", tags=["meta"], summary="项目信息")
def root() -> dict[str, str]:
    return {
        "project": "PlayerStock",
        "message": "PlayerStock API is running",
        "version": settings.app_version,
        "docs": "/docs",
    }


# 统一挂到 /api 前缀下，对应 docs/software/api_contract.md 里的路径
for _module in (health, players, account, trades, positions, prices, ai, debug):
    app.include_router(_module.router, prefix=settings.api_prefix)

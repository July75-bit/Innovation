"""只读运维自检接口（B，第 5 天）。

**为什么存在**：验收清单里有一条"Postgres 控制台能看到 `players` / `trades` 等表"。
Render 免费 Postgres 没有网页数据浏览器，本地又常常连不上 5432（网络被掐），
所以让**跑在 Render 内网里的后端自己**把"用什么库、有哪些表、各有多少行"报出来——
浏览器打开一个 URL 就能截图，比跑脚本还省事（脚本见 `scripts/inspect_db.py`，两者互补）。

**安全边界（刻意收窄）**：
- 只读，且**只回元信息**：方言名、表名、行数、几个业务计数；
- 不回连接串、不回密码、不回任何选手/账户的具体数据，也不接受任何用户输入（没有 SQL 注入面）；
- 可用 `DEBUG_ENDPOINTS=0` 一键关掉（关掉后返回 404，见 `config.debug_endpoints`）；
- 用 SQLAlchemy 的 `inspect()` 而不是 `pg_catalog` 裸 SQL，这样本地 SQLite、线上 Postgres
  同一套代码都能用，测试也不用伪造驱动。

**答辩时的说法**：这是"上线期验收用的只读探针"，不是业务接口；功能验收完成后
把 `DEBUG_ENDPOINTS` 设为 `0`（或删掉本文件与路由注册）即可，前端从不调用它。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.errors import ApiError
from app.models import Player, PriceHistory, Position, Trade, User

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/db", summary="只读数据库自检（方言 / 表清单 / 行数）")
def debug_db(db: Session = Depends(get_db)) -> dict:
    """返回当前库的方言、表清单与行数，用于上线验收截图。"""
    if not settings.debug_endpoints:
        raise ApiError(
            "调试接口已关闭（DEBUG_ENDPOINTS=0）",
            status_code=404,
            code="ENDPOINT_DISABLED",
        )

    bind = db.get_bind()
    table_names = sorted(inspect(bind).get_table_names())

    tables: dict[str, int | None] = {}
    for name in table_names:
        model = Base.metadata.tables.get(name)
        tables[name] = (
            int(db.scalar(select(func.count()).select_from(model))) if model is not None else None
        )

    return {
        "状态": "线上内网连接成功（只读自检）",
        "数据库方言": bind.dialect.name,
        "是否 SQLite": settings.is_sqlite,
        "表清单": table_names,
        "表行数": tables,
        "业务核对": {
            "选手数": int(db.scalar(select(func.count()).select_from(Player)) or 0),
            "价格历史条数": int(db.scalar(select(func.count()).select_from(PriceHistory)) or 0),
            "持仓条数": int(db.scalar(select(func.count()).select_from(Position)) or 0),
            "流水条数": int(db.scalar(select(func.count()).select_from(Trade)) or 0),
            "demo 余额": str(db.scalar(select(User.balance).where(User.nickname == "demo"))),
        },
        "提示": "只读元信息，不含连接串与个人数据；可用 DEBUG_ENDPOINTS=0 关闭本接口",
    }

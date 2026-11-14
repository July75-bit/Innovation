"""运维自检与一次性重灌（B，第 5/6 天）。

**为什么存在**：验收清单里有一条"Postgres 控制台能看到 `players` / `trades` 等表"。
Render 免费 Postgres 没有网页数据浏览器，本地/校园网络又常常连不上 5432（TLS 被掐，
2026-11-07 实测四种环境全灭），所以让**跑在 Render 内网里的后端自己**做两件事：

1. `GET /api/debug/db`：把"用什么库、有哪些表、各有多少行"报出来——浏览器打开就能截图；
2. `POST /api/debug/reseed`（第 6 天补）：一次性**清空重建** 16 人演示数据 + N 轮模拟价
   ——公网连不上库时，重灌走后端内网一次 POST 就完成，演示前还能一键复位。

**安全边界（刻意收窄，两者同口径）**：
- 都属 debug 运维面，`DEBUG_ENDPOINTS=0` 时 404（`config.debug_endpoints`）；
- `/db` 只读、只回元信息，不回连接串、不回密码；
- `/reseed` 必须携带 token（默认 `playerstock-demo-reseed-2026`，`RESEED_TOKEN` 可覆盖），
  错误码 `TOKEN_MISMATCH`；且**破坏性**（drop 全表重建，交易/持仓/流水清零），文档已告知；
- 非业务接口，前端从不调用；功能验收后一起关闭。
"""

from __future__ import annotations

import threading
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from core_engine import generate_match, standardize_score, update_price
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.errors import ApiError
from app.models import Player, PriceHistory, Position, Trade, User

router = APIRouter(prefix="/debug", tags=["debug"])

# 同一时刻只允许一个重灌流程（避免并发把种子写两份）
_RESEED_LOCK = threading.Lock()


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


@router.post(
    "/reseed",
    summary="一次性重灌 16 人演示数据（运维用：清空重建 + N 轮模拟价，需 token）",
)
def debug_reseed(
    db: Session = Depends(get_db),
    token: str = Query(description="口令，等于 settings.reseed_token"),
    rounds: int = Query(default=9, ge=0, le=30, description="模拟轮数；0 = 只写入种子初始价"),
    seed: int = Query(default=42, description="core_engine 的随机种子（同值结果可复现）"),
) -> dict:
    """清空整库并按 `app/core/demo_roster.py`（`data/seed_players.json` 的部署侧镜像）
    重建 16 人演示数据 + N 轮模拟价格。

    为什么做成端点而不是让 B 在本地跑脚本：本服务的 Postgres 走 **Render 内网**，
    而公网直连 5432 常被校园/运营商网络掐断 TLS；让跑在 Render 内网的进程自己灌数，
    一次 POST 就完成，演示前还能一键复位。

    管线（与 `scripts/bootstrap_demo_data.py` 三步同源，进程内实现）：
    1. 清空业务数据（持仓/流水/价格历史/选手）→ **保留 `users`**（BUG-15：注册账号不能被重灌删掉）
       → 重写 16 名选手 + 每人初始价历史（1–2 行）；
    2. 逐轮 `core_engine.generate_match → standardize_score → update_price`
       → `app.core.price_update.plan_for_player + apply_updates`（cascades 从 current_price）；
    3. 自检：trading 选手每人 ≥ 10 点（含负轮回填，与脚本同一约定）。
    """
    if not settings.debug_endpoints:
        raise ApiError(
            "调试接口已关闭（DEBUG_ENDPOINTS=0）",
            status_code=404,
            code="ENDPOINT_DISABLED",
        )
    if token != settings.reseed_token:
        raise ApiError("重灌口令不匹配", status_code=403, code="TOKEN_MISMATCH")
    if _RESEED_LOCK.locked():
        raise ApiError("已有一次重灌在进行中", status_code=409, code="RESEED_BUSY")

    with _RESEED_LOCK:
        from app.core import demo_roster

        cleared = _reseed_tables(db)
        seed_counts = _reseed_demo_rows(db)
        applied_rounds = _simulate_rounds(db, rounds=rounds, seed=seed)
        report = _final_selfcheck(db, rounds=rounds)

    return {
        "状态": "重灌完成" if not report["点数自检"] else "重灌完成（有点数不足项）",
        "schema_version": demo_roster.DEMO_SCHEMA_VERSION,
        "rounds": rounds,
        "seed": seed,
        "行情重置（只动行情与 demo 账户）": cleared,
        "重建": seed_counts,
        "模拟轮次": applied_rounds,
        "点数自检": "OK" if not report["点数自检"] else "；".join(report["点数自检"]),
        "业务核对": {
            "选手数": report["选手数"],
            "战队数": report["战队数"],
            "demo 余额": report["demo 余额"],
        },
        "下一步": "GET /api/players 应为 16 名；**注册账号的余额/持仓/流水全部保留**，只有 demo 演示账户被复位",
        "提示": "重灌只重置行情与 demo 账户；可用 DEBUG_ENDPOINTS=0 关闭本接口",
    }


def _reseed_tables(db: Session) -> dict[str, int]:
    """重置**行情**（价格历史 + 选手行就地更新），**不删** users / positions / trades。

    语义演进（2026-11-07 用户口径）：**账户的余额、持仓、流水永远跟着账号走**，
    与"重置市场行情"是两件独立的事。所以重灌：

    - 价格历史：清掉这 16 名选手的旧点，重新由种子 + N 轮模拟生成；
    - 选手行：**就地 UPDATE**（不删行）——删了会连累 positions / trades 的外键；
    - **users / positions / trades 一律不动**：登录态、余额、持仓、历史流水全部保留；
    - 只有公共演示账户 `demo` 会被复位（见 `_reseed_demo_rows`），否则演示时起点是脏的。
    """
    from sqlalchemy import delete

    from app.core.demo_roster import DEMO_ROSTER

    init_needed = {
        "price_history": 0,
        "players_updated": 0,
        "players_created": 0,
    }
    roster_ids = [int(row["player_id"]) for row in DEMO_ROSTER]

    # 表结构缺失时补齐（新库第一次调用也能用），但**不重建已存在的表**
    from app.core.database import init_db

    init_db()

    # 1) 清掉这 16 人的旧价格历史（持仓/流水不动：它们只记金额与数量，不依赖历史点）
    init_needed["price_history"] = int(
        db.execute(delete(PriceHistory).where(PriceHistory.player_id.in_(roster_ids))).rowcount or 0
    )

    # 2) 选手行就地更新 / 缺失则补建
    from decimal import Decimal as _D

    for row in DEMO_ROSTER:
        pid = int(row["player_id"])
        player = db.get(Player, pid)
        values = {
            "name": str(row["name"]),
            "display_name": str(row.get("display_name") or row["name"]),
            "team": str(row["team"]),
            "role": str(row["role"]),
            "current_price": _D(str(row["current_price"])),
            "prev_price": _D(str(row["initial_price"])),
            "rating": int(row["rating"]),
            "status": str(row["status"]),
        }
        if player is None:
            db.add(Player(player_id=pid, **values))
            init_needed["players_created"] += 1
        else:
            for key, value in values.items():
                setattr(player, key, value)
            init_needed["players_updated"] += 1

    db.commit()
    return init_needed


def _reseed_demo_rows(db: Session) -> dict[str, int]:
    """只复位**公共演示账户 demo**（余额 5000 + 清它的持仓/流水），并写回种子价格历史。

    **注册账号完全不动**：余额、持仓、流水、令牌全部原样保留——这是用户明确要求的口径
    （"每个账户的余额一直保存，跟着账号走，无论什么时候登录都有之前的流水记录"）。
    想清空自己的账户，用户自己点「余额重建」（`POST /api/account/rebuild`）。
    """
    from sqlalchemy import delete

    from app.core.demo_roster import DEMO_ROSTER
    from app.core.time import utcnow

    balance = Decimal(str(settings.initial_balance))

    # 1) demo 账户：有就复位（含清空它的持仓/流水），没有就建
    demo = db.scalar(select(User).where(User.nickname == "demo"))
    if demo is None:
        demo = User(nickname="demo", balance=balance, initial_balance=balance)
        db.add(demo)
        db.flush()
    else:
        demo.balance = balance
    demo_cleared = {
        "positions": int(
            db.execute(delete(Position).where(Position.user_id == demo.user_id)).rowcount or 0
        ),
        "trades": int(
            db.execute(delete(Trade).where(Trade.user_id == demo.user_id)).rowcount or 0
        ),
    }

    # 2) 种子价格历史（每人 1–2 行初始点）
    now = utcnow()
    for row in DEMO_ROSTER:
        player_id = int(row["player_id"])
        initial_price = Decimal(str(row["initial_price"]))
        current_price = Decimal(str(row["current_price"]))
        db.add(
            PriceHistory(player_id=player_id, price=initial_price, reason="初始价格", ts=now)
        )
        if current_price != initial_price:
            db.add(
                PriceHistory(
                    player_id=player_id,
                    price=current_price,
                    reason="行情初始化（种子数据，无对应比赛）",
                    ts=now,
                )
            )

    db.commit()
    return {
        "users": int(db.scalar(select(func.count()).select_from(User)) or 0),
        "demo 账户（余额复位、持仓/流水已清）": 1,
        **{f"demo 清掉的{n}": v for n, v in demo_cleared.items()},
        "players": int(db.scalar(select(func.count()).select_from(Player)) or 0),
        "price_history 种子行": int(
            db.scalar(select(func.count()).select_from(PriceHistory)) or 0
        ),
    }


def _simulate_rounds(db: Session, *, rounds: int, seed: int) -> list[dict]:
    """逐轮模拟价：本轮开价 = 上轮新价（apply_updates 会 cascade current_price）。"""
    from app.core.price_update import apply_updates, plan_for_player
    from app.core.time import utcnow

    players = list(db.scalars(select(Player).order_by(Player.player_id)).all())

    # warmup 与 scripts/update_prices.warmup_history 同约定：负数轮回填最近 3 场（只在内存）
    warmup_by_id: dict[int, list[float]] = {
        player.player_id: [
            generate_match(
                player.player_id,
                seed=seed,
                round_no=-warm,
                base_rating=float(player.rating),
            ).score
            for warm in (3, 2, 1)
        ]
        for player in players
    }
    played_by_id: dict[int, list[float]] = {
        player.player_id: list(warmup_by_id[player.player_id]) for player in players
    }

    applied_rounds: list[dict] = []
    for round_no in range(1, rounds + 1):
        round_ts = utcnow() + timedelta(days=round_no)

        planned_list = []
        for player in players:
            if player.status != "trading":
                continue
            history = played_by_id[player.player_id]
            match = generate_match(
                player.player_id,
                seed=seed,
                round_no=round_no,
                base_rating=float(player.rating),
            )
            signal = standardize_score(match.score, history, window=5)
            played_by_id[player.player_id].append(match.score)

            planned = plan_for_player(
                player,
                # 显式传 score，让 C 的 reason 里能写出本轮得分（契约要求可追溯）
                lambda _price, _s=signal, _sc=match.score: update_price(
                    float(_price), _s, score=_sc
                ),
            )
            planned_list.append(replace(planned, ts=round_ts))

        if planned_list:
            apply_updates(db, planned_list, ts=round_ts)
            applied_rounds.append({"round": round_no, "applied": len(planned_list)})

    return applied_rounds


def _final_selfcheck(db: Session, *, rounds: int) -> dict:
    """与 bootstrap 脚本同一标准：trading 选手每人 ≥ 10 点（还有则列出）。"""
    players = list(db.scalars(select(Player).order_by(Player.player_id)).all())
    short: list[str] = []
    for player in players:
        if player.status != "trading" or rounds <= 0:
            continue
        points = int(
            db.scalar(
                select(func.count(PriceHistory.price_id)).where(
                    PriceHistory.player_id == player.player_id
                )
            )
            or 0
        )
        if points < 10:
            short.append(f"#{player.player_id} {player.name} 只有 {points} 点")

    balance = db.scalar(select(User.balance).where(User.nickname == "demo"))
    return {
        "点数自检": short,
        "选手数": len(players),
        "战队数": len({player.team for player in players}),
        "demo 余额": str(balance),
    }

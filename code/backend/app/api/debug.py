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
from datetime import date, datetime, time, timezone
from decimal import Decimal

from core_engine import generate_match, standardize_score, suspension_reason, update_price
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.errors import ApiError
from app.models import Player, PriceHistory, Position, Trade, User

#: 种子历史点的固定时间戳（开赛前，早于赛程第 1 轮 2026-11-01）。
#: 与 `scripts/seed_db.py` 的 `SEED_TS` 一致：改用固定值后，
#: 「初始价格」不会再排到引擎价格点之后（否则 `/prices` 末点价 != current_price）。
DEMO_SEED_TS = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)

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
    rounds: int = Query(default=12, ge=0, le=30, description="模拟轮数（默认 12：赛程 4 的倍数，每队停 3 轮）"),
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
        "清理（仅业务表，users 保留）": cleared,
        "重建": seed_counts,
        "模拟轮次": applied_rounds,
        "点数自检": "OK" if not report["点数自检"] else "；".join(report["点数自检"]),
        "业务核对": {
            "选手数": report["选手数"],
            "战队数": report["战队数"],
            "demo 余额": report["demo 余额"],
        },
        "下一步": "GET /api/players 应为 16 名；交易/持仓/流水已清零；**注册账号仍可登录**（余额已复位到 5000）",
        "提示": "重灌只复位行情与余额，不删账号；可用 DEBUG_ENDPOINTS=0 关闭本接口",
    }


def _reseed_tables(db: Session) -> dict[str, int]:
    """清空**业务数据**（持仓/流水/价格历史/选手），**保留 `users` 表**。

    2026-11-07 修（BUG-15）：原先这里用 `Base.metadata.drop_all()` 连 `users` 一起删，
    结果是"注册过的私人账号下次重灌就消失"（用户实测第二天登录提示账号不存在）。
    账号数据是用户资产，重灌只该复位行情与交易：
    - 删：positions → trades → price_history → players（按 FK 依赖顺序，先子后父）；
    - **留**：users（用户名 / 口令散列 / 盐 / 令牌行全保留，登录态不失效）；
    - 余额在 `_reseed_demo_rows` 里统一复位（钱跟着行情一起回到起点，见那里的注释）。
    """
    from sqlalchemy import delete

    counts = {
        "positions": 0,
        "trades": 0,
        "price_history": 0,
        "players": 0,
    }
    # 用 SQLAlchemy 的 delete() 而不是裸 SQL：SQLite / Postgres 同一套语义
    for key, model in (
        ("positions", Position),
        ("trades", Trade),
        ("price_history", PriceHistory),
        ("players", Player),
    ):
        counts[key] = int(db.execute(delete(model)).rowcount or 0)

    # 表结构缺失时补齐（新库第一次调用也能用），但**不重建已存在的表**
    from app.core.database import init_db

    init_db()
    db.commit()
    return counts


def _reseed_demo_rows(db: Session) -> dict[str, int]:
    """demo 账户（若缺则建）+ 16 名选手 + 每人初始价历史（口径与 `data/seed_players.json` 一致）。

    **注册账号保留**：只保证 `demo` 存在、并把所有用户的余额复位到 `initial_balance`
    ——行情回到种子价、持仓/流水已清空，钱也一起回到起点才是自洽的；
    用户名、口令散列、令牌都不动，所以重灌后**原来注册的账号仍能直接登录**。
    """
    from app.core.demo_roster import DEMO_ROSTER

    balance = Decimal(str(settings.initial_balance))

    # 1) demo 账户：有就复位，没有就建（不能用 drop 的方式"重建"，会把私人账号一起删掉）
    demo = db.scalar(select(User).where(User.nickname == "demo"))
    if demo is None:
        db.add(User(nickname="demo", balance=balance, initial_balance=balance))
    else:
        demo.balance = balance

    # 2) 其它注册账号：余额复位，登录凭据（password_hash / salt）与令牌行原样保留
    reset_users = 0
    for user in db.scalars(select(User).where(User.nickname != "demo")).all():
        user.balance = Decimal(str(settings.initial_balance))
        reset_users += 1

    now = DEMO_SEED_TS
    for row in DEMO_ROSTER:
        player_id = int(row["player_id"])
        initial_price = Decimal(str(row["initial_price"]))
        current_price = Decimal(str(row["current_price"]))
        db.add(
            Player(
                player_id=player_id,
                name=str(row["name"]),
                display_name=str(row.get("display_name") or row["name"]),
                team=str(row["team"]),
                role=str(row["role"]),
                current_price=current_price,
                prev_price=initial_price,
                rating=int(row["rating"]),
                status=str(row["status"]),
            )
        )
        db.flush()
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
        "注册账号（已复位余额、保留凭据）": reset_users,
        "players": int(db.scalar(select(func.count()).select_from(Player)) or 0),
        "price_history 种子行": int(
            db.scalar(select(func.count()).select_from(PriceHistory)) or 0
        ),
    }


def _simulate_rounds(db: Session, *, rounds: int, seed: int) -> list[dict]:
    """逐轮模拟价：本轮开价 = 上轮新价（apply_updates 会 cascade current_price）。"""
    from app.core.price_update import apply_updates, plan_for_player

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
    from app.core.demo_schedule import DEMO_SCHEDULE

    schedule_matches = DEMO_SCHEDULE["matches"]
    for round_no in range(1, rounds + 1):
        # 时间戳取赛程里的比赛日（与 scripts/simulate_match.py 的 ts 口径一致）
        meta = schedule_matches[(round_no - 1) % len(schedule_matches)]
        round_ts = datetime.combine(
            date.fromisoformat(meta["played_at"]), time.min, tzinfo=timezone.utc
        )

        planned_list = []
        for player in players:
            # 暂停交易：手动 status 优先，其次看本队这一轮是否有比赛（整队停牌）
            if suspension_reason(
                {"status": player.status, "team": player.team}, round_no, DEMO_SCHEDULE
            ):
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

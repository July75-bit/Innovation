"""惰性自动结算：免费档方案 A 的最终形态（2026-11-28 调整版）。

负责人：B（写库链路复用 app.core.price_update）/ 定价公式始终走 C 的 core_engine

**为什么调整**：Render 免费档不支持 cron 服务（蓝图里 `type: cron` + `plan: free`
的服务创建会直接失败），"外部定时器每天打 recalc"落不了地；而"重灌"
（reseed / bootstrap）会清掉用户、持仓与成交，不能当日常机制。

**现在怎么做**：`settle_if_due` 挂在三个"顺路"入口——
- 应用启动（lifespan，冷唤醒即补）；
- `GET /api/players`（市场页首访）；
- `GET /api/players/{id}/prices`（详情页曲线）。
每个入口先过两道快速闸门：节流（默认 ≥300s 才检查一次）+ 一条
`SELECT max(ts)`（没到期就到此为止）。真正做遍历重放的只有"跨天后第一次访问"
这一次，微秒级数学 + 若干次写库，用户几乎无感。

**链条必须和线上已有点位一致**（否则曲线接缝跳变）：
- 与 `scripts/simulate_match.py` / `scripts/settle_round.py` 同参数：
  seed=42、window=5、warmup=3，从第 1 轮全链重放，只落"库里没有"的轮次；
- 选手取自 **players 表**（rating/team/status 现读），不是 data/seed_players.json——
  后端容器 rootDir=code/backend，没有仓库 data 目录；赛程用 `app/core/demo_schedule.py` 镜像；
- 落库走 `plan_for_player + apply_updates`（players 与 price_history 同事务），
  去重键与 `POST /api/prices/recalc` 完全一致：`(player_id, 比赛日 UTC)`。

**开关与口径**（config.py，环境变量大写同名）：
- AUTO_SETTLE：总开关，默认 **0**（关闭）——线上在 render.yaml 设 1；测试环境天然不受影响；
- AUTO_SETTLE_SEED / _WINDOW / _WARMUP：复现链参数，改动 = 换剧本，需整链重灌；
- AUTO_SETTLE_START_DATE：赛季首日（第 1 轮的日期），与 build_schedule.py 一致；
- AUTO_SETTLE_AS_OF：日期覆盖（YYYY-MM-DD），**只用于演示"时间快进"**，线上留空；
- AUTO_SETTLE_MIN_INTERVAL：两次检查的最小间隔秒数。

**边界**：第 29 轮起对阵按赛程循环（suspension_reason 取模），比赛日按天顺延——
演示季不过季；空库（没 reseed 过）不补，留给人工初始化。
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import date, datetime, time as dtime, timedelta, timezone
from typing import Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core_engine import generate_match, standardize_score, suspension_reason, update_price

from app.core.config import settings
from app.core.database import get_db
from app.core.demo_schedule import DEMO_SCHEDULE
from app.core.price_update import apply_updates, plan_for_player
from app.models import Player, PriceHistory

logger = logging.getLogger("playerstock.auto_settle")

#: 同一实例多线程（uvicorn threadpool）同时命中时，只让一个线程做补算
_lock = threading.Lock()
_last_check: float | None = None  # time.monotonic() 基准


# ---------------------------------------------------------------- 轮次换算
def _start_date() -> date:
    return date.fromisoformat(settings.auto_settle_start_date)


def _play_date(round_no: int) -> date:
    """轮次 → 比赛日（UTC 零点口径）：第 1 轮 = 赛季首日，之后每日一轮。"""
    return _start_date() + timedelta(days=round_no - 1)


def _round_of(day: date) -> int:
    """日期 → 已结算轮次；早于赛季返回 0（只有种子点，一轮没算过）。"""
    return max(0, (day - _start_date()).days + 1)


def _as_of() -> date:
    override = (settings.auto_settle_as_of or "").strip()
    if override:
        return date.fromisoformat(override)
    return datetime.now(timezone.utc).date()


# ---------------------------------------------------------------- 结算主体
def _roster(player: Player) -> dict[str, Any]:
    """把 ORM 对象转成 core_engine 暂停判定吃的字典形状。"""
    return {"player_id": int(player.player_id), "team": player.team, "status": player.status}


def _settle_range(db: Session, first: int, target: int) -> int:
    """重放第 1..target 轮的信号链，落库第 first..target 轮，返回补算轮数。"""
    players = list(db.scalars(select(Player).order_by(Player.player_id)).all())
    if not players:
        return 0  # 空库：连 reseed 都没跑过，不越权造数据

    seed, window, warmup = (
        settings.auto_settle_seed,
        settings.auto_settle_window,
        settings.auto_settle_warmup,
    )
    # 与 simulate_match.warmup_history 对应：负数轮次只在内存，不写库
    history: dict[int, list[float]] = {
        int(p.player_id): [
            generate_match(
                int(p.player_id), seed=seed, round_no=n, base_rating=float(p.rating or 0)
            ).score
            for n in range(-warmup, 0)
        ]
        for p in players
    }

    settled = 0
    for round_no in range(1, target + 1):
        day = _play_date(round_no)
        round_ts = datetime.combine(day, dtime.min, tzinfo=timezone.utc)
        next_ts = round_ts + timedelta(days=1)
        planned = []
        for p in players:
            if suspension_reason(_roster(p), round_no, DEMO_SCHEDULE):
                continue  # 队伍比赛 / 手动冻结：本轮无点（与 recalc 一致）
            match = generate_match(
                int(p.player_id),
                seed=seed,
                round_no=round_no,
                played_at=day.isoformat(),
                base_rating=float(p.rating or 0),
            )
            hist = history[int(p.player_id)]
            signal = standardize_score(match.score, hist, window=window)
            hist.append(match.score)  # 停牌者不进历史——链条与 bootstrap 相同
            if round_no < first:
                continue
            dup = db.scalar(
                select(func.count(PriceHistory.price_id)).where(
                    PriceHistory.player_id == p.player_id,
                    PriceHistory.ts >= round_ts,
                    PriceHistory.ts < next_ts,
                )
            )
            if dup:
                continue  # 与 recalc 同键去重：重放无害
            def calculator(price: float, _s: float = signal, _sc: float = match.score):
                return update_price(float(price), _s, score=_sc)

            planned.append(plan_for_player(p, calculator))
        if planned:
            # apply_updates 提交后 ORM 实例过期，下一轮读到的就是新 current_price
            apply_updates(db, planned, ts=round_ts)
            settled += 1
    return settled


def settle_if_due(db: Session, *, force: bool = False) -> str:
    """入口函数：返回本次检查的结论字符串（off/throttled/busy/up-to-date/settled:N）。

    永不抛业务异常进请求链路由调用方保证——本函数内部的异常会直接上抛，
    `settle_now`（依赖）与 lifespan 都做了兜底捕获。
    """
    global _last_check
    if not settings.auto_settle:
        return "off"
    if not force and _last_check is not None:
        if time.monotonic() - _last_check < settings.auto_settle_min_interval:
            return "throttled"
    if not _lock.acquire(blocking=False):
        return "busy"
    try:
        max_ts = db.scalar(select(func.max(PriceHistory.ts)))
        _last_check = time.monotonic()
        if max_ts is None:
            return "empty-db"
        last, target = _round_of(max_ts.date()), _round_of(_as_of())
        if target <= last:
            return "up-to-date"
        settled = _settle_range(db, last + 1, target)
        logger.info(
            "惰性自动结算：第 %d~%d 轮补算 %d 轮（作为 %s）",
            last + 1, target, settled, _as_of().isoformat(),
        )
        return f"settled:{settled}"
    finally:
        _lock.release()


# ---------------------------------------------------------------- 请求侧胶水
def settle_now(db: Session = Depends(get_db)) -> None:
    """FastAPI 依赖：只读接口"顺手"触发补算，任何异常都不影响接口本身。"""
    try:
        settle_if_due(db)
    except Exception:  # noqa: BLE001 - 结算失败绝不拖垮页面，留日志排查
        logger.warning("惰性自动结算异常（已忽略，不影响本次请求）", exc_info=True)


__all__ = ["settle_if_due", "settle_now"]
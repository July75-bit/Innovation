"""价格与行情历史接口（B 提供接口，数据由 C 的定价模块产生）。

负责人：B + C

GET /api/players/{player_id}/prices
- 时间升序，前端折线图直接按数组顺序画；
- 每条必须带 reason（涨跌归因）；
- 选手不存在 → 404 PLAYER_NOT_FOUND；选手存在但无历史 → 200 + points: []。

POST /api/prices/recalc（第 4 天新增，C 负责定价与去重逻辑）
- 由"赛后结算"调用：一次提交一轮里所有选手的得分 + 信号 S(t)；
- 定价只用 C 的 `core_engine.update_price`（reason 里带"本轮得分"），
  落库仍走 B 的 `app.core.price_update`（本模块不写 SQL）；
- **幂等**：同一 `(player_id, round)` 只落一次，重复调用返回 `skipped` 而不是再写一行；
  实现上把 `played_at`（比赛日期）写进 `price_history.ts`，用它作为轮次的可查键；
- 暂停交易（`status != trading`）、同请求内重复的选手 → 记入 `skipped`，不影响其它选手。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone

from core_engine import update_price
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError
from app.core.price_update import apply_updates, plan_for_player
from app.models import Player, PriceHistory
from app.schemas.price import (
    PriceHistoryResponse,
    PricePoint,
    PriceRecalcApplied,
    PriceRecalcRequest,
    PriceRecalcResponse,
    PriceRecalcSkipped,
)

router = APIRouter(tags=["prices"])


def _round_ts(played_at: date) -> datetime:
    """把比赛日期转成该轮在 `price_history.ts` 里的时间戳（UTC 零点）。"""
    return datetime.combine(played_at, time.min, tzinfo=timezone.utc)



@router.get(
    "/players/{player_id}/prices",
    response_model=PriceHistoryResponse,
    summary="选手价格历史（升序，空数组不 404）",
)
def get_price_history(
    player_id: int, db: Session = Depends(get_db)
) -> PriceHistoryResponse:
    if db.get(Player, player_id) is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    rows = db.scalars(
        select(PriceHistory)
        .where(PriceHistory.player_id == player_id)
        .order_by(PriceHistory.ts.asc(), PriceHistory.price_id.asc())
    ).all()

    return PriceHistoryResponse(
        player_id=player_id,
        points=[
            PricePoint(ts=row.ts, price=float(row.price), reason=row.reason)
            for row in rows
        ],
    )


@router.post(
    "/prices/recalc",
    response_model=PriceRecalcResponse,
    summary="按轮次重算价格（幂等：同一 (player_id, round) 只落一次）",
)
def recalc_prices(
    payload: PriceRecalcRequest, db: Session = Depends(get_db)
) -> PriceRecalcResponse:
    """赛后结算：一轮里每名选手提交一次 (score, S)，算价并落库。

    去重键为 `(player_id, round)`：`round` 由 `played_at` 体现（每轮一个比赛日），
    已存在的 `price_history` 行会被跳过，因此同一份数据重放多少次结果都一样。
    """
    round_ts = _round_ts(payload.played_at)
    next_ts = round_ts + timedelta(days=1)

    applied: list[PriceRecalcApplied] = []
    skipped: list[PriceRecalcSkipped] = []
    handled: set[int] = set()

    for item in payload.items:
        if item.player_id in handled:
            skipped.append(
                PriceRecalcSkipped(
                    player_id=item.player_id, reason="同一请求内重复出现，已忽略"
                )
            )
            continue
        handled.add(item.player_id)

        player = db.get(Player, item.player_id)
        if player is None:
            raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")
        if player.status != "trading":
            skipped.append(
                PriceRecalcSkipped(
                    player_id=item.player_id,
                    reason=f"选手状态 {player.status}，跳过定价",
                )
            )
            continue

        already = db.scalar(
            select(func.count(PriceHistory.price_id)).where(
                PriceHistory.player_id == item.player_id,
                PriceHistory.ts >= round_ts,
                PriceHistory.ts < next_ts,
            )
        )
        if already:
            skipped.append(
                PriceRecalcSkipped(
                    player_id=item.player_id,
                    reason="该轮已计价（按 (player_id, round) 去重）",
                )
            )
            continue

        signal, score = item.signal, item.score

        def calculator(price: float, _s: float = signal, _sc: float = score):
            """把 C 的定价函数包成 B 的落库服务要的 calculator 形态。"""
            return update_price(float(price), _s, score=_sc)

        planned = replace(plan_for_player(player, calculator), ts=round_ts)
        apply_updates(db, [planned], ts=round_ts)

        applied.append(
            PriceRecalcApplied(
                player_id=planned.player_id,
                old_price=float(planned.old_price),
                new_price=float(planned.new_price),
                change_pct=planned.change_pct,
                reason=planned.reason,
            )
        )

    return PriceRecalcResponse(
        round_no=payload.round_no, applied=applied, skipped=skipped
    )


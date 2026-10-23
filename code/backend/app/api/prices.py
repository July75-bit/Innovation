"""价格与行情历史接口（B 提供接口，数据由 C 的定价模块产生）。

负责人：B + C

GET /api/players/{player_id}/prices
- 时间升序，前端折线图直接按数组顺序画；
- 每条必须带 reason（涨跌归因）；
- 选手不存在 → 404 PLAYER_NOT_FOUND；选手存在但无历史 → 200 + points: []。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Player, PriceHistory
from app.schemas.price import PriceHistoryResponse, PricePoint

router = APIRouter(tags=["prices"])


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

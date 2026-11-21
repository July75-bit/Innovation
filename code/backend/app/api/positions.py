"""持仓接口。

负责人：B（实现） / A（前端展示）

GET /api/positions
- 只返回 quantity > 0 的持仓，按 player_id 升序；
- avg_cost 为加权买入均价（接口输出保留 2 位）；
- market_value = current_price × quantity；
- profit = market_value − avg_cost × quantity；profit_pct = profit / 成本 × 100。
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Player, Position, User
from app.schemas.position import PositionItem

router = APIRouter(prefix="/positions", tags=["positions"])

CENT = Decimal("0.01")


@router.get("", response_model=list[PositionItem], summary="当前持仓列表")
def list_positions(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[PositionItem]:
    rows = db.execute(
        select(Position, Player)
        .join(Player, Position.player_id == Player.player_id)
        .where(Position.user_id == user.user_id, Position.quantity > 0)
        .order_by(Position.player_id)
    ).all()

    items: list[PositionItem] = []
    for position, player in rows:
        quantity = int(position.quantity)
        cost = (Decimal(position.avg_cost) * quantity).quantize(CENT)
        market_value = (Decimal(player.current_price) * quantity).quantize(CENT)
        profit = (market_value - cost).quantize(CENT)
        profit_pct = float((profit / cost * Decimal(100)).quantize(CENT)) if cost > 0 else 0.0

        items.append(
            PositionItem(
                player_id=player.player_id,
                name=player.name,
                quantity=quantity,
                avg_cost=float(Decimal(position.avg_cost).quantize(CENT)),
                current_price=float(player.current_price),
                market_value=float(market_value),
                profit=float(profit),
                profit_pct=profit_pct,
            )
        )
    return items

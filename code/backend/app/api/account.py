"""账户接口。

负责人：B

GET /api/account —— 当前用户虚拟币余额与总资产：
- balance：可用虚拟币；
- initial_balance：初始 5000，用于算总收益率；
- position_value：持仓按当前价合计的市值；
- total_asset：balance + position_value。
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Player, Position, User
from app.schemas.account import AccountResponse

router = APIRouter(prefix="/account", tags=["account"])

CENT = Decimal("0.01")


@router.get("", response_model=AccountResponse, summary="账户余额与总资产")
def get_account(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> AccountResponse:
    rows = db.execute(
        select(Position.quantity, Player.current_price).join(
            Player, Position.player_id == Player.player_id
        ).where(Position.user_id == user.user_id, Position.quantity > 0)
    ).all()

    position_value = sum(
        (Decimal(price) * int(quantity) for quantity, price in rows), Decimal("0")
    ).quantize(CENT)

    balance = Decimal(user.balance).quantize(CENT)
    return AccountResponse(
        user_id=user.user_id,
        balance=float(balance),
        initial_balance=float(Decimal(user.initial_balance).quantize(CENT)),
        position_value=float(position_value),
        total_asset=float((balance + position_value).quantize(CENT)),
    )

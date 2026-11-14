"""账户接口。

负责人：B

GET /api/account —— 当前用户虚拟币余额与总资产：
- balance：可用虚拟币；
- initial_balance：初始 5000，用于算总收益率；
- position_value：持仓按当前价合计的市值；
- total_asset：balance + position_value。

POST /api/account/rebuild —— **余额重建**（用户自助）：把自己这个账户恢复成"刚注册"的样子
（余额回到 5000、清空自己的持仓与流水）。账号本身、口令、其它账号一律不动。
为什么需要：重置市场行情（`POST /api/debug/reseed`）现在**不会**动任何注册账号
（余额/持仓/流水跟着账号走），所以"我想重新开始"必须由用户自己按一下。
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Player, Position, Trade, User
from app.schemas.account import AccountRebuildResponse, AccountResponse

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


@router.post(
    "/rebuild",
    response_model=AccountRebuildResponse,
    summary="重建余额（把自己这个账户恢复成刚注册的样子）",
)
def rebuild_account(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    confirm: bool = Query(default=False, description="必须显式传 confirm=true，防误触"),
) -> AccountRebuildResponse:
    """**只作用于当前登录的账户**：余额 → `initial_balance`，清空自己的持仓与流水。

    - 公共演示账户（无令牌时的 demo）也允许重建——它就是给大家试用的；
    - 幂等：重复调用结果一致（第二次清掉 0 条）；
    - 不影响其它账号、不影响行情与选手数据。
    """
    if not confirm:
        raise ApiError("请显式确认（confirm=true）后再重建余额", status_code=400, code="CONFIRM_REQUIRED")

    cleared_positions = int(
        db.execute(delete(Position).where(Position.user_id == user.user_id)).rowcount or 0
    )
    cleared_trades = int(
        db.execute(delete(Trade).where(Trade.user_id == user.user_id)).rowcount or 0
    )

    initial = Decimal(str(user.initial_balance)).quantize(CENT)
    user.balance = initial
    db.commit()
    db.refresh(user)

    return AccountRebuildResponse(
        user_id=user.user_id,
        balance=float(Decimal(user.balance).quantize(CENT)),
        cleared_positions=cleared_positions,
        cleared_trades=cleared_trades,
        note="余额已恢复为初始值；本账户的持仓与流水已清空（其它账号与行情不受影响）",
    )

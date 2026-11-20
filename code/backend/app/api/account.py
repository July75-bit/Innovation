"""账户接口。

负责人：B

GET /api/account —— 当前用户信用点余额与总资产：
- balance：可用信用点；
- initial_balance：初始 5000，用于算总收益率；
- position_value：持仓按当前价合计的市值；
- total_asset：balance + position_value。

POST /api/account/rebuild —— **余额重建**（用户自助）：把自己这个账户恢复成"刚注册"的样子
（余额回到 5000、清空自己的持仓与流水）。账号本身、口令、其它账号一律不动。
为什么需要：重置市场行情（`POST /api/debug/reseed`）现在**不会**动任何注册账号
（余额/持仓/流水跟着账号走），所以"我想重新开始"必须由用户自己按一下。
"""

from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Player, Position, PriceHistory, Trade, User
from app.schemas.account import (
    AccountHistoryResponse,
    AccountRebuildResponse,
    AccountResponse,
    AccountStats,
    AssetPoint,
)

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


def _epoch(dt: datetime) -> float:
    """把可能被 SQLite 读成 naive 的时间统一成 UTC 时间戳。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


@router.get("/history", response_model=AccountHistoryResponse, summary="资产曲线与统计")
def get_account_history(
    days: int = Query(default=30, ge=1, le=365, description="回看多少天"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AccountHistoryResponse:
    """个人页用：按时间重建「现金 + 持仓市值」曲线，并汇总交易统计。

    - 数据只来自**本账户**的流水 + 全市场历史价格（价格是公共数据）；
    - 曲线点 = 历史价格时间点 ∪ 交易时间点 ∪ 现在；没有交易时是一条 5000 的水平线；
    - 最后一个点用当前余额/当前持仓对齐 `GET /api/account`，保证两处数字一致。
    """
    initial = Decimal(str(user.initial_balance)).quantize(CENT)
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - days * 86400

    trades = list(
        db.scalars(
            select(Trade).where(Trade.user_id == user.user_id).order_by(Trade.created_at)
        ).all()
    )
    trade_epochs = [(_epoch(trade.created_at), trade) for trade in trades]

    # 每个选手的 (时间戳, 价格) 序列，供任意时刻取"最近一次已知价格"
    price_rows = db.execute(
        select(PriceHistory.player_id, PriceHistory.ts, PriceHistory.price).order_by(
            PriceHistory.ts
        )
    ).all()
    series: dict[int, list[tuple[float, float]]] = {}
    price_epochs: set[float] = set()
    for player_id, ts, price in price_rows:
        epoch = _epoch(ts)
        series.setdefault(int(player_id), []).append((epoch, float(price)))
        price_epochs.add(epoch)
    for rows in series.values():
        rows.sort(key=lambda item: item[0])

    current_prices = {
        int(player_id): float(price)
        for player_id, price in db.execute(select(Player.player_id, Player.current_price)).all()
    }

    def price_at(player_id: int, epoch: float) -> float:
        rows = series.get(player_id)
        if not rows:
            return current_prices.get(player_id, 0.0)
        epochs = [row[0] for row in rows]
        index = bisect_right(epochs, epoch) - 1
        if index < 0:
            index = 0
        return rows[index][1]

    timeline = sorted(
        {epoch for epoch in price_epochs if epoch >= cutoff}
        | {epoch for epoch, _ in trade_epochs if epoch >= cutoff}
        | {now.timestamp()}
    )

    points: list[AssetPoint] = []
    last_epoch = timeline[-1]
    for epoch in timeline:
        cash = float(initial)
        holdings: dict[int, int] = {}
        for trade_epoch, trade in trade_epochs:
            if trade_epoch > epoch:
                break
            amount = float(trade.amount)
            quantity = int(trade.quantity)
            player_id = int(trade.player_id)
            if trade.side == "BUY":
                cash -= amount
                holdings[player_id] = holdings.get(player_id, 0) + quantity
            else:
                cash += amount
                holdings[player_id] = holdings.get(player_id, 0) - quantity

        if abs(epoch - last_epoch) < 1e-6:
            # 最后一点直接用当前账户值，和 GET /api/account 完全对齐
            account = get_account(db=db, user=user)
            cash = account.balance
            position_value = account.position_value
        else:
            position_value = sum(
                max(quantity, 0) * price_at(player_id, epoch)
                for player_id, quantity in holdings.items()
            )
        points.append(
            AssetPoint(
                ts=datetime.fromtimestamp(epoch, tz=timezone.utc),
                cash=round(cash, 2),
                position_value=round(position_value, 2),
                total_asset=round(cash + position_value, 2),
            )
        )

    account = get_account(db=db, user=user)
    buys = [trade for trade in trades if trade.side == "BUY"]
    sells = [trade for trade in trades if trade.side == "SELL"]
    position_rows = db.execute(
        select(Position.quantity, Player.current_price)
        .join(Player, Position.player_id == Player.player_id)
        .where(Position.user_id == user.user_id, Position.quantity > 0)
    ).all()
    return AccountHistoryResponse(
        initial_balance=float(initial),
        points=points,
        stats=AccountStats(
            trades=len(trades),
            buys=len(buys),
            sells=len(sells),
            buy_amount=round(sum(float(trade.amount) for trade in buys), 2),
            sell_amount=round(sum(float(trade.amount) for trade in sells), 2),
            positions=len(position_rows),
            position_value=account.position_value,
            profit=round(account.total_asset - float(initial), 2),
        ),
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

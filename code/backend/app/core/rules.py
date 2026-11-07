"""交易规则（纯函数，不碰数据库，可单测）。

规则来源：docs/software/api_contract.md §4.7/§4.8 与 database_design.md §3。
- 数量必须是正整数（由 Pydantic 层拦，见 schemas.TradeRequest）；
- 金额 = 成交价 × 数量，按分四舍五入；
- 余额不足不允许买入，持仓不足不允许卖出（不允许卖空）；
- 单选手持仓上限 settings.max_position_per_player（默认 50 股）；
- 比赛中的选手（status = suspended）暂停交易。

数据库写入在 app/api/trades.py，余额/持仓/流水必须同事务提交。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.core.config import settings
from app.core.errors import ApiError

CENT = Decimal("0.01")

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"


def calc_amount(price: Decimal | float | str, quantity: int) -> Decimal:
    """成交金额，保留两位小数。"""
    price_dec = price if isinstance(price, Decimal) else Decimal(str(price))
    return (price_dec * Decimal(quantity)).quantize(CENT, rounding=ROUND_HALF_UP)


def ensure_tradable(status: str) -> None:
    """只有 trading 状态可以买卖。"""
    if status != "trading":
        raise ApiError(
            "该选手比赛进行中，暂停交易，请等结算完成后重试",
            status_code=400,
            code="PLAYER_TRADING_SUSPENDED",
        )


def ensure_sufficient_balance(
    balance: Decimal,
    amount: Decimal,
    *,
    price: Decimal | None = None,
) -> None:
    """余额不足时给出"下一步"：按当前价最多还能买几股。

    只报"余额不足，需要 X"会让用户不知道该怎么办（Nielsen「错误可恢复：原因 + 下一步」）；
    传入 `price` 时补一句可买股数，前端可以直接照抄这句话展示。
    """
    if balance >= amount:
        return

    hint = ""
    if price is not None and price > 0:
        affordable = int(balance // price)
        if affordable > 0:
            hint = f"；按当前价 {price:.2f}，最多可买 {affordable} 股"
        else:
            hint = f"；当前余额买不起 1 股（当前价 {price:.2f}）"

    raise ApiError(
        f"余额不足，当前余额 {balance:.2f}，需要 {amount:.2f}{hint}",
        status_code=400,
        code="INSUFFICIENT_BALANCE",
    )


def ensure_available_position(held: int, quantity: int) -> None:
    """持仓不足时同样给"下一步"：最多能卖多少、以及没有持仓时该怎么办。"""
    if held >= quantity:
        return

    if held <= 0:
        hint = "；当前没有该选手的持仓，请先买入"
    else:
        hint = f"；最多可卖 {held} 股，可改成卖出 {held} 股或先买入更多"

    raise ApiError(
        f"持仓不足，当前持有 {held} 股，本次卖出 {quantity} 股{hint}",
        status_code=400,
        code="INSUFFICIENT_POSITION",
    )


def ensure_position_limit(
    current_quantity: int, buy_quantity: int, limit: int | None = None
) -> None:
    """超过单选手上限时告诉用户"还能买几股"，而不是只报一个 50。"""
    limit = settings.max_position_per_player if limit is None else limit
    if current_quantity + buy_quantity <= limit:
        return

    remaining = max(limit - current_quantity, 0)
    if remaining > 0:
        hint = f"；最多还能买 {remaining} 股（上限 {limit} 股）"
    else:
        hint = f"；已持满 {limit} 股，需先卖出才能再买"

    raise ApiError(
        f"超过单选手持仓上限 {limit} 股，当前持有 {current_quantity} 股，"
        f"本次买入 {buy_quantity} 股{hint}",
        status_code=400,
        code="POSITION_LIMIT_EXCEEDED",
    )

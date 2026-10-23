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


def ensure_sufficient_balance(balance: Decimal, amount: Decimal) -> None:
    if balance < amount:
        raise ApiError(
            f"余额不足，当前余额 {balance:.2f}，需要 {amount:.2f}",
            status_code=400,
            code="INSUFFICIENT_BALANCE",
        )


def ensure_available_position(held: int, quantity: int) -> None:
    if held < quantity:
        raise ApiError(
            f"持仓不足，当前持有 {held} 股，本次卖出 {quantity} 股",
            status_code=400,
            code="INSUFFICIENT_POSITION",
        )


def ensure_position_limit(
    current_quantity: int, buy_quantity: int, limit: int | None = None
) -> None:
    limit = settings.max_position_per_player if limit is None else limit
    if current_quantity + buy_quantity > limit:
        raise ApiError(
            f"超过单选手持仓上限 {limit} 股，当前持有 {current_quantity} 股，"
            f"本次买入 {buy_quantity} 股",
            status_code=400,
            code="POSITION_LIMIT_EXCEEDED",
        )

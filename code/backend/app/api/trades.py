"""买入 / 卖出 / 交易流水。

负责人：B（实现） / A（前端调用） / C（成交价来源）

契约见 docs/software/api_contract.md §4.7–§4.9：

- POST /api/trades/buy   买入
- POST /api/trades/sell  卖出
- GET  /api/trades       交易流水（时间倒序）

校验顺序（契约 §4.7，前端依赖这个顺序给提示）：
1. player_id 存在 → 否则 404 PLAYER_NOT_FOUND
2. quantity 为正整数 → 由 Pydantic 拦截 → 422 VALIDATION_ERROR
3. 选手 status == trading → 否则 400 PLAYER_TRADING_SUSPENDED
4. 余额充足 → 否则 400 INSUFFICIENT_BALANCE
5. 买入后持仓 ≤ 50 → 否则 400 POSITION_LIMIT_EXCEEDED
6. 事务内扣款 + 加持仓 + 写流水 → COMMIT

成交价一律用数据库里的 current_price（最新价），不使用任何缓存价。

并发与事务：
- 进程内 _trade_lock 串行化下单，避免同一账户并发扣款；
- 扣款用 `UPDATE ... WHERE balance >= amount` 条件更新，多进程下也不会扣成负数；
- 余额、持仓、流水在同一个事务提交，任一步失败整体 rollback。
"""

from __future__ import annotations

import logging
import threading
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.rules import (
    CENT,
    SIDE_BUY,
    SIDE_SELL,
    calc_amount,
    ensure_available_position,
    ensure_position_limit,
    ensure_sufficient_balance,
    ensure_tradable,
)
from app.models import Player, Position, Trade, User
from app.schemas.trade import TradeItem, TradeRequest, TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])

logger = logging.getLogger("playerstock.trades")

COST_PRECISION = Decimal("0.0001")
_trade_lock = threading.Lock()


def _get_player(db: Session, player_id: int) -> Player:
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")
    return player


def _record_trade(
    db: Session,
    *,
    user_id: int,
    player_id: int,
    side: str,
    price: Decimal,
    quantity: int,
    amount: Decimal,
    balance_after: Decimal,
) -> Trade:
    """写一条流水（单独成函数，便于测试事务回滚）。"""
    trade = Trade(
        user_id=user_id,
        player_id=player_id,
        side=side,
        quantity=quantity,
        price=price,
        amount=amount,
        balance_after=balance_after,
    )
    db.add(trade)
    db.flush()
    return trade


@router.post("/buy", response_model=TradeResponse, summary="买入选手")
def buy(
    payload: TradeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradeResponse:
    player = _get_player(db, payload.player_id)
    ensure_tradable(player.status)

    quantity = payload.quantity
    price = Decimal(player.current_price).quantize(CENT)
    amount = calc_amount(price, quantity)

    with _trade_lock:
        current_user = db.get(User, user.user_id, populate_existing=True)
        position = db.scalar(
            select(Position).where(
                Position.user_id == current_user.user_id,
                Position.player_id == player.player_id,
            )
        )
        held = int(position.quantity) if position else 0

        # 先做规则校验，全部通过才动数据库
        ensure_position_limit(held, quantity)
        ensure_sufficient_balance(Decimal(current_user.balance), amount)

        try:
            deducted = db.execute(
                update(User)
                .where(User.user_id == current_user.user_id, User.balance >= amount)
                .values(balance=User.balance - amount)
            )
            if deducted.rowcount != 1:
                db.rollback()
                raise ApiError(
                    f"余额不足，当前余额 {Decimal(current_user.balance):.2f}，"
                    f"需要 {amount:.2f}",
                    status_code=400,
                    code="INSUFFICIENT_BALANCE",
                )

            db.refresh(current_user)
            new_balance = Decimal(current_user.balance).quantize(CENT)

            if position is None:
                position = Position(
                    user_id=current_user.user_id,
                    player_id=player.player_id,
                    quantity=quantity,
                    avg_cost=price,
                )
                db.add(position)
            else:
                total_cost = Decimal(position.avg_cost) * held + amount
                position.quantity = held + quantity
                position.avg_cost = (total_cost / Decimal(position.quantity)).quantize(
                    COST_PRECISION, rounding=ROUND_HALF_UP
                )

            db.flush()
            trade = _record_trade(
                db,
                user_id=current_user.user_id,
                player_id=player.player_id,
                side=SIDE_BUY,
                price=price,
                quantity=quantity,
                amount=amount,
                balance_after=new_balance,
            )
            db.commit()
        except ApiError:
            db.rollback()
            raise
        except Exception as exc:  # pragma: no cover - 兜底，避免把堆栈发给前端
            db.rollback()
            logger.exception(
                "买入失败 user_id=%s player_id=%s", user.user_id, payload.player_id
            )
            raise ApiError("交易失败，请稍后重试", status_code=500, code="INTERNAL_ERROR") from exc

    return TradeResponse(
        success=True,
        message="买入成功",
        balance=float(new_balance),
        player_id=player.player_id,
        quantity=quantity,
        price=float(price),
        trade_id=trade.trade_id,
    )


@router.post("/sell", response_model=TradeResponse, summary="卖出选手")
def sell(
    payload: TradeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradeResponse:
    player = _get_player(db, payload.player_id)
    ensure_tradable(player.status)

    quantity = payload.quantity
    price = Decimal(player.current_price).quantize(CENT)
    amount = calc_amount(price, quantity)

    with _trade_lock:
        current_user = db.get(User, user.user_id, populate_existing=True)
        position = db.scalar(
            select(Position).where(
                Position.user_id == current_user.user_id,
                Position.player_id == player.player_id,
            )
        )
        held = int(position.quantity) if position else 0
        ensure_available_position(held, quantity)

        try:
            db.execute(
                update(User)
                .where(User.user_id == current_user.user_id)
                .values(balance=User.balance + amount)
            )
            db.refresh(current_user)
            new_balance = Decimal(current_user.balance).quantize(CENT)

            if held == quantity:
                # 清仓：删行（positions.quantity 有 1–50 的 CHECK，不能留 0）
                db.delete(position)
            else:
                position.quantity = held - quantity

            db.flush()
            trade = _record_trade(
                db,
                user_id=current_user.user_id,
                player_id=player.player_id,
                side=SIDE_SELL,
                price=price,
                quantity=quantity,
                amount=amount,
                balance_after=new_balance,
            )
            db.commit()
        except ApiError:
            db.rollback()
            raise
        except Exception as exc:  # pragma: no cover - 兜底，避免把堆栈发给前端
            db.rollback()
            logger.exception(
                "卖出失败 user_id=%s player_id=%s", user.user_id, payload.player_id
            )
            raise ApiError("交易失败，请稍后重试", status_code=500, code="INTERNAL_ERROR") from exc

    return TradeResponse(
        success=True,
        message="卖出成功",
        balance=float(new_balance),
        player_id=player.player_id,
        quantity=quantity,
        price=float(price),
        trade_id=trade.trade_id,
    )


@router.get("", response_model=list[TradeItem], summary="交易流水（倒序）")
def list_trades(
    limit: int = Query(50, ge=1, le=200, description="最多返回条数"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TradeItem]:
    rows = db.execute(
        select(Trade, Player)
        .join(Player, Trade.player_id == Player.player_id)
        .where(Trade.user_id == user.user_id)
        .order_by(Trade.created_at.desc(), Trade.trade_id.desc())
        .limit(limit)
    ).all()

    return [
        TradeItem(
            trade_id=trade.trade_id,
            player_id=trade.player_id,
            name=player.name,
            side=trade.side,
            quantity=int(trade.quantity),
            price=float(trade.price),
            amount=float(trade.amount),
            balance_after=float(trade.balance_after),
            created_at=trade.created_at,
        )
        for trade, player in rows
    ]

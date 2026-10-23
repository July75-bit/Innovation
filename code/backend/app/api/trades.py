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

并发与事务（第 2 天加固；答辩问"并发下怎么保证不超卖"就看这三条）：
1. 进程内 `_trade_lock` 先把同一进程的下单排队，只是减少无谓的写冲突；
2. 真正的正确性靠数据库的**条件更新**，不靠"读出来再判断"：
   - 扣款 `UPDATE users SET balance = balance - amount WHERE balance >= amount`；
   - 加仓 `UPDATE positions SET quantity = quantity + n WHERE quantity + n <= 50`；
   - 减仓 `UPDATE positions SET quantity = quantity - n WHERE quantity >= n`。
   读出来的余额/持仓只用于拼中文提示，条件成不成立以数据库当时的行为准；
3. 买入先扣款、卖出先入账（都先拿账户行），再动持仓，两条路径的加锁顺序一致，
   不会互相死锁；任一步失败整体 rollback，失败时钱和货一起回到原样。

为什么不能只靠"读出来判断"：两个连接（多进程 / 多 worker）可以同时读到"持仓 3 股"，
各自都判断"卖 2 股够"，结果卖掉 4 股、钱按 4 股入账。条件更新把判断交给数据库，
第二个 UPDATE 的 WHERE 不成立就一行都不改，于是"钱货二选一"必然失败。
"""

from __future__ import annotations

import logging
import threading
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
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
    limit = settings.max_position_per_player

    with _trade_lock:
        current_user = db.get(User, user.user_id, populate_existing=True)
        user_id = current_user.user_id

        try:
            # 契约 §4.7 第 4 步：余额。先扣款——rowcount 为 0 就是余额不够；
            # 这条 UPDATE 同时把账户行的写锁握在手里，后面读到的持仓一定是最新值。
            deducted = db.execute(
                update(User)
                .where(User.user_id == user_id, User.balance >= amount)
                .values(balance=User.balance - amount)
            )
            if deducted.rowcount != 1:
                db.rollback()
                balance_now = Decimal(db.get(User, user_id, populate_existing=True).balance)
                ensure_sufficient_balance(balance_now, amount)
                raise ApiError("交易失败，请稍后重试", status_code=500, code="INTERNAL_ERROR")

            db.refresh(current_user)
            new_balance = Decimal(current_user.balance).quantize(CENT)

            # 契约 §4.7 第 5 步：持仓上限。读出来只为拼提示，真正的判断在 UPDATE 的 WHERE 里。
            position = db.scalar(
                select(Position)
                .where(Position.user_id == user_id, Position.player_id == player.player_id)
                .execution_options(populate_existing=True)
            )
            held = int(position.quantity) if position else 0
            ensure_position_limit(held, quantity)

            if position is None:
                db.add(
                    Position(
                        user_id=user_id,
                        player_id=player.player_id,
                        quantity=quantity,
                        avg_cost=price,
                    )
                )
                db.flush()
            else:
                # 条件加仓：把"加完不超过 50 股"交给数据库判断，
                # 两个连接同时加仓时第二个必然 rowcount=0，不会合计超上限。
                grown = db.execute(
                    update(Position)
                    .where(
                        Position.user_id == user_id,
                        Position.player_id == player.player_id,
                        Position.quantity + quantity <= limit,
                    )
                    .values(quantity=Position.quantity + quantity)
                )
                if grown.rowcount != 1:
                    db.rollback()
                    fresh = db.scalar(
                        select(Position).where(
                            Position.user_id == user_id,
                            Position.player_id == player.player_id,
                        )
                    )
                    ensure_position_limit(int(fresh.quantity) if fresh else 0, quantity)
                    raise ApiError("交易失败，请稍后重试", status_code=500, code="INTERNAL_ERROR")

                # 加仓成功后再算均价：此时数量已是最新值，用 Decimal 计算避免浮点误差。
                updated = db.scalar(
                    select(Position)
                    .where(Position.user_id == user_id, Position.player_id == player.player_id)
                    .execution_options(populate_existing=True)
                )
                new_quantity = int(updated.quantity)
                cost_before = Decimal(updated.avg_cost) * (new_quantity - quantity)
                updated.avg_cost = ((cost_before + amount) / Decimal(new_quantity)).quantize(
                    COST_PRECISION, rounding=ROUND_HALF_UP
                )
                db.flush()

            trade = _record_trade(
                db,
                user_id=user_id,
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
        user_id = current_user.user_id

        try:
            # 1) 先入账：拿账户行的写锁，和买入保持同一加锁顺序（避免互相死锁）。
            #    入账之后如果发现持仓不够，下面的 rollback 会把这笔钱一起撤销。
            db.execute(
                update(User).where(User.user_id == user_id).values(balance=User.balance + amount)
            )
            db.refresh(current_user)
            new_balance = Decimal(current_user.balance).quantize(CENT)

            # 2) 锁内重读持仓，读出来只用于拼中文提示。
            position = db.scalar(
                select(Position)
                .where(Position.user_id == user_id, Position.player_id == player.player_id)
                .execution_options(populate_existing=True)
            )
            held = int(position.quantity) if position else 0
            ensure_available_position(held, quantity)

            # 3) 条件减仓：`quantity > n` 是"不允许卖空"的权威防线。
            #    两个连接同时卖同一批股票时，第二个必然 rowcount=0，只能拿到 400。
            shrunk = db.execute(
                update(Position)
                .where(
                    Position.user_id == user_id,
                    Position.player_id == player.player_id,
                    Position.quantity > quantity,
                )
                .values(quantity=Position.quantity - quantity)
            )
            if shrunk.rowcount != 1:
                # 4) 一次卖光：直接删行（positions.quantity 有 1–50 的 CHECK，
                #    写成 0 会违反约束，所以清仓必须走 DELETE，且同样用 `= n` 做原子判断）。
                cleared = db.execute(
                    delete(Position).where(
                        Position.user_id == user_id,
                        Position.player_id == player.player_id,
                        Position.quantity == quantity,
                    )
                )
                if cleared.rowcount != 1:
                    db.rollback()
                    fresh = db.scalar(
                        select(Position).where(
                            Position.user_id == user_id,
                            Position.player_id == player.player_id,
                        )
                    )
                    ensure_available_position(int(fresh.quantity) if fresh else 0, quantity)
                    raise ApiError("交易失败，请稍后重试", status_code=500, code="INTERNAL_ERROR")

            trade = _record_trade(
                db,
                user_id=user_id,
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

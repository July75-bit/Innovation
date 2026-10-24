"""并发一致性测试：多连接下不允许超卖、超上限、余额变负。

负责人：B

为什么需要这一组用例：`_trade_lock` 只在**单个进程内**有效——线上跑多 worker、
多实例，或者用户开了两个标签页，两个数据库连接完全可能同时读到同一份持仓，
各自都判断"卖 2 股够"，最后卖掉 4 股、钱却按 4 股入账（第 2 天实测复现过：
持有 3 股卖出了 4 股，余额从 5000.00 变成 5504.00）。

这里不靠多线程撞运气，而是用两个独立 Session 把"读-读-写-写"的交错**稳定复现**：

- 连接 B 先把持仓读进自己的 identity map（旧值）；
- 连接 A 先成交并提交（数据库已变）；
- 连接 B 再拿着旧值下单。

正确实现必须让 B 拿到 400，并且"钱 + 货"守恒。对应风险清单 R4 与
NFR-C-01，把第 4 天的并发门禁提前到第 2 天。
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.api import trades as trades_module
from app.core.errors import ApiError
from app.models import Position, User
from app.schemas.trade import TradeRequest

# 与 tests/conftest.py 的固定演示数据对应
SEED_ZYWOO = 1  # 126.00
SEED_FLAMEZ = 8  # 63.00


def _sold_quantity(client, player_id: int) -> int:
    """统计某选手累计卖出的股数（用于验证钱货守恒）。"""
    rows = client.get("/api/trades").json()
    return sum(t["quantity"] for t in rows if t["side"] == "SELL" and t["player_id"] == player_id)


def _position_row(session, player_id: int) -> Position | None:
    return session.scalar(
        select(Position).where(Position.user_id == 1, Position.player_id == player_id)
    )


def test_two_connections_cannot_oversell(client, session_factory) -> None:
    """两个连接各卖 2 股、实际只有 3 股时，后一个必须被拒绝。"""
    assert client.post(
        "/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 3}
    ).status_code == 200

    conn_a = session_factory()
    conn_b = session_factory()
    try:
        # B 先读到 3 股（模拟另一个进程/worker 早一步查询）
        stale = _position_row(conn_b, SEED_ZYWOO)
        assert int(stale.quantity) == 3

        # A 卖掉 2 股并提交，数据库只剩 1 股；余额 5000 - 3×126 + 2×126 = 4874.00
        resp_a = trades_module.sell(
            TradeRequest(player_id=SEED_ZYWOO, quantity=2),
            db=conn_a,
            user=conn_a.get(User, 1),
        )
        assert float(resp_a.balance) == pytest.approx(4874.00)

        # B 拿旧值再卖 2 股：钱和货只能二选一，必须失败
        with pytest.raises(ApiError) as excinfo:
            trades_module.sell(
                TradeRequest(player_id=SEED_ZYWOO, quantity=2),
                db=conn_b,
                user=conn_b.get(User, 1),
            )
        assert excinfo.value.code == "INSUFFICIENT_POSITION"
        assert excinfo.value.status_code == 400
    finally:
        conn_a.close()
        conn_b.close()

    # 钱货守恒：只成交 2 股，剩 1 股，余额只加 2 股的钱
    assert client.get("/api/account").json()["balance"] == pytest.approx(4874.00)
    positions = client.get("/api/positions").json()
    assert len(positions) == 1
    assert positions[0]["quantity"] == 1
    assert _sold_quantity(client, SEED_ZYWOO) == 2
    # 卖掉的 2 股 + 剩下的 1 股 = 最初买入的 3 股
    assert _sold_quantity(client, SEED_ZYWOO) + positions[0]["quantity"] == 3


def test_two_connections_cannot_exceed_position_limit(client, session_factory) -> None:
    """两个连接各买 2 股、上限只剩 2 股时，后一个必须被拒绝。"""
    # 先买到 48 股：63.00 × 48 = 3024.00，余额足够
    assert client.post(
        "/api/trades/buy", json={"player_id": SEED_FLAMEZ, "quantity": 48}
    ).status_code == 200

    conn_a = session_factory()
    conn_b = session_factory()
    try:
        stale = _position_row(conn_b, SEED_FLAMEZ)
        assert int(stale.quantity) == 48

        # A 买到 50 股（正好顶满上限），余额 5000 - 50×63 = 1850.00
        resp_a = trades_module.buy(
            TradeRequest(player_id=SEED_FLAMEZ, quantity=2),
            db=conn_a,
            user=conn_a.get(User, 1),
        )
        assert float(resp_a.balance) == pytest.approx(1850.00)

        # B 拿旧值 48 再买 2 股：数据库已是 50，必须被拒
        with pytest.raises(ApiError) as excinfo:
            trades_module.buy(
                TradeRequest(player_id=SEED_FLAMEZ, quantity=2),
                db=conn_b,
                user=conn_b.get(User, 1),
            )
        assert excinfo.value.code == "POSITION_LIMIT_EXCEEDED"
    finally:
        conn_a.close()
        conn_b.close()

    assert client.get("/api/positions").json()[0]["quantity"] == 50
    assert client.get("/api/account").json()["balance"] == pytest.approx(1850.00)


def test_two_connections_cannot_overdraw_balance(client, session_factory) -> None:
    """两个连接各买 25 股（合计 6300.00 > 5000.00）时，后一个必须被拒绝。"""
    conn_a = session_factory()
    conn_b = session_factory()
    try:
        # A 先买 25 股：25 × 126.00 = 3150.00，余额剩 1850.00
        resp_a = trades_module.buy(
            TradeRequest(player_id=SEED_ZYWOO, quantity=25),
            db=conn_a,
            user=conn_a.get(User, 1),
        )
        assert float(resp_a.balance) == pytest.approx(1850.00)

        # B 再买 25 股：25 + 25 = 50 没有超上限，但余额已经不够
        with pytest.raises(ApiError) as excinfo:
            trades_module.buy(
                TradeRequest(player_id=SEED_ZYWOO, quantity=25),
                db=conn_b,
                user=conn_b.get(User, 1),
            )
        assert excinfo.value.code == "INSUFFICIENT_BALANCE"
        assert excinfo.value.status_code == 400
    finally:
        conn_a.close()
        conn_b.close()

    # 余额不允许为负，持仓只加了 25 股
    balance = Decimal(str(client.get("/api/account").json()["balance"]))
    assert balance == Decimal("1850.00")
    assert balance >= 0
    assert client.get("/api/positions").json()[0]["quantity"] == 25

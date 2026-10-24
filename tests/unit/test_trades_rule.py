"""交易规则边界测试（B 的 D1/D4 验收点）。

负责人：B

分工文档要求测试"余额不足、持仓不足、非法数量、无效选手、持仓上限、暂停交易"，
全部通过才算交易系统交付。这里覆盖买入、卖出、最新价、事务回滚四类关键路径。

约定：每个用例一个独立临时库（见 tests/conftest.py），不读写 playerstock.db。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

# 与 tests/conftest.py 的固定演示数据对应
SEED_ZYWOO = 1
SEED_SH1RO = 7
# flameZ：63.00 一股，用来构造"只超上限、不超余额"的场景
SEED_FLAMEZ = 8


def _buy(client, player_id: int, quantity: int):
    return client.post("/api/trades/buy", json={"player_id": player_id, "quantity": quantity})


def _sell(client, player_id: int, quantity: int):
    return client.post("/api/trades/sell", json={"player_id": player_id, "quantity": quantity})


def test_buy_normal(client) -> None:
    """正常买入：余额减少、持仓增加、生成一条 BUY 流水。"""
    response = _buy(client, SEED_ZYWOO, 2)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "买入成功"
    assert body["balance"] == pytest.approx(4748.00)
    assert body["player_id"] == SEED_ZYWOO
    assert body["quantity"] == 2
    assert body["price"] == 126.00
    assert body["trade_id"] > 0

    account = client.get("/api/account").json()
    assert account["balance"] == pytest.approx(4748.00)
    assert account["position_value"] == pytest.approx(252.00)
    assert account["total_asset"] == pytest.approx(5000.00)

    positions = client.get("/api/positions").json()
    assert len(positions) == 1
    assert positions[0]["quantity"] == 2
    assert positions[0]["avg_cost"] == pytest.approx(126.00)

    trades = client.get("/api/trades").json()
    assert len(trades) == 1
    assert trades[0]["side"] == "BUY"
    assert trades[0]["quantity"] == 2
    assert trades[0]["amount"] == pytest.approx(252.00)
    assert trades[0]["balance_after"] == pytest.approx(4748.00)


def test_buy_insufficient_balance(client) -> None:
    """余额不足 -> 400，且余额、持仓、流水都不变。"""
    # 50 股 × 126.00 = 6300.00 > 5000.00（未触发持仓上限，先命中余额不足）
    response = _buy(client, SEED_ZYWOO, 50)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INSUFFICIENT_BALANCE"
    assert "余额不足" in body["message"]

    assert client.get("/api/account").json()["balance"] == pytest.approx(5000.00)
    assert client.get("/api/positions").json() == []
    assert client.get("/api/trades").json() == []


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2"])
def test_buy_invalid_quantity(client, quantity) -> None:
    """quantity 为 0 / 负数 / 小数 / 非数字 -> 422 或 400。"""
    response = _buy(client, SEED_ZYWOO, quantity)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert "请求参数不合法" in body["message"]


def test_buy_invalid_player(client) -> None:
    """选手不存在 -> 404。"""
    response = _buy(client, 999, 1)

    assert response.status_code == 404
    assert response.json()["code"] == "PLAYER_NOT_FOUND"
    assert response.json()["message"] == "选手不存在"


def test_buy_exceeds_position_limit(client) -> None:
    """单选手持仓超过 50 股 -> 400。

    用 63.00 一股的 flameZ，保证两次买入之后余额仍然充足，
    这样只有"持仓上限"一条规则被违反，测的是上限而不是余额。
    """
    assert _buy(client, SEED_FLAMEZ, 30).status_code == 200

    # 30 + 25 = 55 > 50；25 × 63.00 = 1575.00 < 剩余余额，不触发余额不足
    response = _buy(client, SEED_FLAMEZ, 25)
    assert response.status_code == 400
    assert response.json()["code"] == "POSITION_LIMIT_EXCEEDED"
    assert "持仓上限" in response.json()["message"]

    assert client.get("/api/positions").json()[0]["quantity"] == 30


def test_buy_checks_balance_before_position_limit(client, session_factory) -> None:
    """契约 §4.7 第 4 步（余额）必须早于第 5 步（持仓上限）报错。

    前端按 code 给提示，顺序错了会提示"超过持仓上限"，
    用户其实真正的问题是没钱——这条用例把顺序钉死。
    """
    from decimal import Decimal

    from sqlalchemy import select

    from app.models import Position, User

    with session_factory() as db:
        user = db.scalar(select(User).where(User.nickname == "demo"))
        user.balance = Decimal("50.00")
        db.add(
            Position(
                user_id=user.user_id,
                player_id=SEED_FLAMEZ,
                quantity=49,
                avg_cost=Decimal("63.00"),
            )
        )
        db.commit()

    # 同时违反两条：余额 50.00 < 2 × 63.00，且 49 + 2 = 51 > 50
    response = _buy(client, SEED_FLAMEZ, 2)

    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_BALANCE"
    assert "余额不足" in response.json()["message"]

    # 失败后钱和货都不许变
    assert client.get("/api/account").json()["balance"] == pytest.approx(50.00)
    assert client.get("/api/positions").json()[0]["quantity"] == 49


def test_buy_suspended_player(client) -> None:
    """比赛中（status = suspended）的选手买入 -> 400。"""
    response = _buy(client, SEED_SH1RO, 1)

    assert response.status_code == 400
    assert response.json()["code"] == "PLAYER_TRADING_SUSPENDED"
    assert "暂停交易" in response.json()["message"]


def test_sell_more_than_held(client) -> None:
    """卖出数量大于持仓 -> 400，不允许卖空。"""
    assert _buy(client, SEED_ZYWOO, 2).status_code == 200

    response = _sell(client, SEED_ZYWOO, 3)
    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_POSITION"
    assert client.get("/api/positions").json()[0]["quantity"] == 2


def test_sell_normal(client) -> None:
    """正常卖出：余额增加、持仓减少或归零、生成一条 SELL 流水。"""
    assert _buy(client, SEED_ZYWOO, 2).status_code == 200

    response = _sell(client, SEED_ZYWOO, 1)
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "卖出成功"
    assert body["balance"] == pytest.approx(4874.00)

    positions = client.get("/api/positions").json()
    assert positions[0]["quantity"] == 1

    trades = client.get("/api/trades").json()
    assert [trade["side"] for trade in trades] == ["SELL", "BUY"]

    # 全部卖出后持仓行删除，回归空列表
    assert _sell(client, SEED_ZYWOO, 1).status_code == 200
    assert client.get("/api/positions").json() == []
    assert client.get("/api/account").json()["balance"] == pytest.approx(5000.00)


def test_trade_uses_latest_price(client, session_factory) -> None:
    """价格更新后成交必须用最新价，不能用户缓存价。"""
    assert _buy(client, SEED_ZYWOO, 1).status_code == 200

    # 模拟 C 的定价模块把价格从 126 调到 130
    from app.models import Player

    with session_factory() as db:
        player = db.get(Player, SEED_ZYWOO)
        player.current_price = Decimal("130.00")
        db.commit()

    response = _buy(client, SEED_ZYWOO, 1)
    assert response.status_code == 200
    assert response.json()["price"] == 130.00

    position = client.get("/api/positions").json()[0]
    assert position["quantity"] == 2
    # (126 + 130) / 2 = 128
    assert position["avg_cost"] == pytest.approx(128.00)


def test_transaction_rollback_on_failure(client, monkeypatch) -> None:
    """事务一致性：买入失败时余额、持仓、流水三者都不能被部分修改。"""
    import app.api.trades as trades_module

    def _boom(*args, **kwargs):
        raise RuntimeError("模拟写流水失败")

    monkeypatch.setattr(trades_module, "_record_trade", _boom)

    response = _buy(client, SEED_ZYWOO, 2)
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"

    # 扣款与加持仓必须一并回滚
    assert client.get("/api/account").json()["balance"] == pytest.approx(5000.00)
    assert client.get("/api/positions").json() == []
    assert client.get("/api/trades").json() == []

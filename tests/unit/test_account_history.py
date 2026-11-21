"""个人页数据源：GET /api/account/history 的回归测试。

守三件事：
1. 没有交易时曲线是「初始资产水平线」，不报错；
2. 买入后：统计（笔数/金额/持仓）对得上，曲线最后一点与 GET /api/account 完全一致；
3. 参数边界：days 非法返回 422。
"""

from __future__ import annotations

import pytest

SEED_ZYWOO = 1


def test_history_without_trades_is_flat_initial_balance(client) -> None:
    body = client.get("/api/account/history").json()

    assert body["initial_balance"] == pytest.approx(5000.00)
    assert len(body["points"]) >= 1
    for point in body["points"]:
        assert point["total_asset"] == pytest.approx(5000.00)
        assert point["cash"] == pytest.approx(5000.00)
        assert point["position_value"] == pytest.approx(0.00)

    stats = body["stats"]
    assert stats["trades"] == 0
    assert stats["buys"] == 0
    assert stats["sells"] == 0
    assert stats["positions"] == 0
    assert stats["profit"] == pytest.approx(0.00)


def test_history_after_buy_matches_account_and_stats(client) -> None:
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 10})

    account = client.get("/api/account").json()
    body = client.get("/api/account/history").json()

    last = body["points"][-1]
    assert last["total_asset"] == pytest.approx(account["total_asset"])
    assert last["cash"] == pytest.approx(account["balance"])
    assert last["position_value"] == pytest.approx(account["position_value"])
    # 时间戳必须升序（前端折线直接用）
    timestamps = [point["ts"] for point in body["points"]]
    assert timestamps == sorted(timestamps)

    stats = body["stats"]
    assert stats["trades"] == 1
    assert stats["buys"] == 1
    assert stats["sells"] == 0
    assert stats["positions"] == 1
    assert stats["buy_amount"] == pytest.approx(1260.00)
    assert stats["sell_amount"] == pytest.approx(0.00)
    assert stats["profit"] == pytest.approx(account["total_asset"] - 5000.00)


def test_history_days_must_be_positive(client) -> None:
    assert client.get("/api/account/history?days=0").status_code == 422
    assert client.get("/api/account/history?days=999").status_code == 422

"""交易接口的**返回内容契约**测试（day2 文档点名的 test_api_trades.py）。

负责人：B

分工（避免和 `test_trades_rule.py` 重叠）：
- 本文件守"字段集合和类型"——前端拿到 `undefined` 就崩，这类事故靠这里挡；
- `test_trades_rule.py` 守"业务规则与边界"——余额不足、持仓不足、超上限等；
- `test_trades_concurrency.py` 守"并发下钱货守恒"。

对应 day2 最容易翻车的第 1 条：**B 返回字段和契约不一致**（契约 §4.7/§4.8/§4.9）。
"""

from __future__ import annotations

import re

import pytest

# 与 tests/conftest.py 的固定演示数据对应：ZywOo 126.00，demo 余额 5000.00
SEED_ZYWOO = 1
SEED_SH1RO = 7  # status = suspended

BUY_KEYS = {
    "success",
    "message",
    "balance",
    "player_id",
    "quantity",
    "price",
    "trade_id",
}
TRADE_ITEM_KEYS = {
    "trade_id",
    "player_id",
    "name",
    "side",
    "quantity",
    "price",
    "amount",
    "balance_after",
    "created_at",
}
ERROR_KEYS = {"success", "message", "code"}


def _buy(client, quantity: int = 2):
    return client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": quantity})


def _sell(client, quantity: int = 1):
    return client.post("/api/trades/sell", json={"player_id": SEED_ZYWOO, "quantity": quantity})


def test_buy_response_matches_contract(client) -> None:
    """买入成功响应：字段集合、类型、金额两位小数都要与契约 §4.7 一致。"""
    response = _buy(client, 2)
    assert response.status_code == 200

    body = response.json()
    assert set(body) == BUY_KEYS, f"买入响应字段与契约不一致：{set(body) ^ BUY_KEYS}"
    assert "id" not in body, "契约规定选手主键叫 player_id，不叫 id"

    assert body["success"] is True
    assert body["message"] == "买入成功"
    assert isinstance(body["player_id"], int)
    assert isinstance(body["quantity"], int)
    assert isinstance(body["trade_id"], int) and body["trade_id"] > 0
    # 126.00 × 2 = 252.00；5000.00 - 252.00 = 4748.00
    assert body["price"] == pytest.approx(126.00)
    assert body["balance"] == pytest.approx(4748.00)
    assert round(body["balance"], 2) == body["balance"], "金额必须保留两位小数"


def test_sell_response_matches_contract(client) -> None:
    """卖出成功响应：与买入同构，只有 message 不同（契约 §4.8）。"""
    assert _buy(client, 2).status_code == 200

    response = _sell(client, 1)
    assert response.status_code == 200

    body = response.json()
    assert set(body) == BUY_KEYS
    assert body["success"] is True
    assert body["message"] == "卖出成功"
    assert body["balance"] == pytest.approx(4874.00)
    assert body["trade_id"] > 0


def test_trade_item_matches_contract(client) -> None:
    """流水条目：字段集合、side 取值、amount 勾稽、ISO 8601 UTC 时间（契约 §4.9）。"""
    assert _buy(client, 2).status_code == 200

    items = client.get("/api/trades").json()
    assert len(items) == 1

    item = items[0]
    assert set(item) == TRADE_ITEM_KEYS, f"流水字段与契约不一致：{set(item) ^ TRADE_ITEM_KEYS}"
    assert "type" not in item and "direction" not in item, "契约规定方向字段叫 side"
    assert "qty" not in item and "num" not in item, "契约规定数量字段叫 quantity"

    assert item["side"] in {"BUY", "SELL"}
    assert item["side"] == "BUY"
    assert item["name"] == "ZywOo"
    assert item["price"] == pytest.approx(126.00)
    assert item["quantity"] == 2
    # 金额勾稽：amount = price × quantity
    assert item["amount"] == pytest.approx(item["price"] * item["quantity"])
    # balance_after 必须存在且等于成交后余额
    assert item["balance_after"] == pytest.approx(4748.00)
    # 时间统一 ISO 8601 UTC，以 Z 结尾，前端 new Date() 可直接解析
    assert item["created_at"].endswith("Z")
    assert "T" in item["created_at"]


def test_trade_list_is_descending(client) -> None:
    """流水必须按时间倒序（契约 §4.9），同一秒内按 trade_id 兜底。"""
    assert _buy(client, 1).status_code == 200
    assert _buy(client, 1).status_code == 200
    assert _sell(client, 1).status_code == 200

    items = client.get("/api/trades").json()
    assert len(items) == 3

    ids = [item["trade_id"] for item in items]
    assert ids == sorted(ids, reverse=True), f"流水不是倒序：{ids}"

    times = [item["created_at"] for item in items]
    assert times == sorted(times, reverse=True), f"流水时间不是倒序：{times}"

    # 最新一笔一定是 SELL，最旧一笔一定是 BUY
    assert items[0]["side"] == "SELL"
    assert items[-1]["side"] == "BUY"


def test_latest_trade_balance_after_equals_account(client) -> None:
    """最近一笔流水的 balance_after 必须等于当前账户余额（对账口径，day2 15:30 任务）。"""
    assert _buy(client, 2).status_code == 200
    assert _sell(client, 1).status_code == 200

    latest = client.get("/api/trades").json()[0]
    account = client.get("/api/account").json()

    assert latest["balance_after"] == pytest.approx(account["balance"])
    assert account["balance"] == pytest.approx(4874.00)


def test_error_body_matches_contract(client) -> None:
    """所有失败都必须返回同一套 {success, message, code}（契约 §2）。

    多一个字段少一个字段，前端就要写映射表——这里把四条错误路径的形状钉死。
    """
    cases = [
        (
            "余额不足",
            client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 50}),
            400,
            "INSUFFICIENT_BALANCE",
        ),
        (
            "持仓不足",
            client.post("/api/trades/sell", json={"player_id": SEED_ZYWOO, "quantity": 1}),
            400,
            "INSUFFICIENT_POSITION",
        ),
        (
            "暂停交易",
            client.post("/api/trades/buy", json={"player_id": SEED_SH1RO, "quantity": 1}),
            400,
            "PLAYER_TRADING_SUSPENDED",
        ),
        (
            "无效选手",
            client.post("/api/trades/buy", json={"player_id": 999, "quantity": 1}),
            404,
            "PLAYER_NOT_FOUND",
        ),
        (
            "非法数量",
            client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 0}),
            422,
            "VALIDATION_ERROR",
        ),
    ]

    for name, resp, expected_status, expected_code in cases:
        assert resp.status_code == expected_status, f"{name} 状态码不对"
        body = resp.json()
        assert set(body) == ERROR_KEYS, f"{name} 错误体字段与契约不一致：{set(body) ^ ERROR_KEYS}"
        assert body["success"] is False
        assert body["code"] == expected_code, f"{name} 的 code 不对"
        # message 必须是可直接展示的中文，前端不写映射表
        assert re.search(r"[\u4e00-\u9fff]", body["message"]), (
            f"{name} 的 message 不是中文：{body['message']}"
        )

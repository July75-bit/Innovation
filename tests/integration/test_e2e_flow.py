"""端到端集成测试：一条主链路打通前后端依赖的全部接口。

负责人：D（牵头） + B（接口）

主链路（第 3 天必须跑通，第 5 天线上再验一次）：

    GET  /api/players           拿市场列表
    GET  /api/account           拿初始余额 5000
    POST /api/trades/buy        买入 2 股
    GET  /api/positions         持仓出现该选手
    GET  /api/trades            流水里有一条 BUY
    GET  /api/players/{id}/prices  价格历史非空
    POST /api/trades/sell       卖出 1 股
    GET  /api/account           余额比买入后增加
    GET  /api/analysis/{id}     返回合法结构的建议（AI 或 rule_fallback 均可）

数据来自 `tests/conftest.py` 的临时库（4 名选手：ZywOo 120→126 / ropz 横盘 /
sh1ro 停牌 / flameZ 70→63），不读写仓库里的 playerstock.db。
"""

from __future__ import annotations

import json

import ai.llm_agent
import pytest
from app.core.config import settings

SEED_ZYWOO = 1
INITIAL_BALANCE = 5000.0
ZYWOO_PRICE = 126.0
ZYWOO_PREV_PRICE = 120.0
QUANTITY = 2

ADVICE_KEYS = {
    "player_id",
    "action",
    "reason",
    "risk_level",
    "source",
    "disclaimer",
}
VALID_ACTIONS = {"BUY", "SELL", "HOLD"}
VALID_RISKS = {"LOW", "MEDIUM", "HIGH"}
VALID_SOURCES = {"llm", "rule_fallback"}


def _assert_valid_advice(body: dict, player_id: int) -> None:
    assert set(body) == ADVICE_KEYS
    assert "suggested_price_band" not in body
    assert body["player_id"] == player_id
    assert body["action"] in VALID_ACTIONS
    assert body["risk_level"] in VALID_RISKS
    assert body["source"] in VALID_SOURCES
    assert 0 < len(body["reason"]) <= 120
    assert body["disclaimer"]


@pytest.mark.integration
def test_full_trade_flow(client, monkeypatch) -> None:
    """完整交易闭环：查行情 → 买入 → 看持仓 → 卖出 → 余额与流水同步变化。"""
    monkeypatch.setattr(settings, "llm_api_key", "")  # AI 走规则版，测试不碰网络

    # ---------- 1. 查行情 ----------
    market_response = client.get("/api/players")
    assert market_response.status_code == 200
    market = market_response.json()
    assert len(market) == 4

    zywoo = next(player for player in market if player["player_id"] == SEED_ZYWOO)
    assert zywoo["name"] == "ZywOo"
    assert zywoo["current_price"] == ZYWOO_PRICE
    assert zywoo["prev_price"] == ZYWOO_PREV_PRICE
    assert zywoo["change_pct"] == 5.0
    assert zywoo["status"] == "trading"

    # 折线图数据：升序、每点带 reason
    price_response = client.get(f"/api/players/{SEED_ZYWOO}/prices")
    assert price_response.status_code == 200
    points = price_response.json()["points"]
    assert len(points) >= 2
    assert all(point["reason"] for point in points)
    assert [point["price"] for point in points] == [ZYWOO_PREV_PRICE, ZYWOO_PRICE]

    # ---------- 2. 初始账户 ----------
    account = client.get("/api/account").json()
    assert account["balance"] == INITIAL_BALANCE
    assert account["initial_balance"] == INITIAL_BALANCE
    assert account["position_value"] == 0.0
    assert account["total_asset"] == INITIAL_BALANCE

    # ---------- 3. 买入 2 股 ----------
    buy_response = client.post(
        "/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": QUANTITY}
    )
    assert buy_response.status_code == 200
    buy = buy_response.json()
    assert buy["success"] is True
    assert buy["price"] == ZYWOO_PRICE
    assert buy["quantity"] == QUANTITY
    assert buy["balance"] == INITIAL_BALANCE - ZYWOO_PRICE * QUANTITY  # 4748.0

    # ---------- 4. 持仓出现该选手 ----------
    positions = client.get("/api/positions").json()
    assert len(positions) == 1
    held = positions[0]
    assert held["player_id"] == SEED_ZYWOO
    assert held["quantity"] == QUANTITY
    assert held["avg_cost"] == ZYWOO_PRICE
    assert held["market_value"] == ZYWOO_PRICE * QUANTITY
    assert held["profit"] == 0.0

    # 流水里有一条 BUY
    trades = client.get("/api/trades").json()
    assert len(trades) == 1
    assert trades[0]["side"] == "BUY"
    assert trades[0]["player_id"] == SEED_ZYWOO
    assert trades[0]["quantity"] == QUANTITY
    assert trades[0]["amount"] == ZYWOO_PRICE * QUANTITY

    # ---------- 5. 卖出 1 股 ----------
    sell_response = client.post(
        "/api/trades/sell", json={"player_id": SEED_ZYWOO, "quantity": 1}
    )
    assert sell_response.status_code == 200
    sell = sell_response.json()
    assert sell["success"] is True
    assert sell["price"] == ZYWOO_PRICE
    # 4748.0 + 126.0
    assert sell["balance"] == INITIAL_BALANCE - ZYWOO_PRICE * (QUANTITY - 1)  # 4874.0

    # ---------- 6. 卖后：余额增加、持仓减少、流水倒序 ----------
    account_after = client.get("/api/account").json()
    assert account_after["balance"] == 4874.0
    assert account_after["position_value"] == ZYWOO_PRICE  # 剩 1 股
    assert account_after["total_asset"] == 5000.0

    positions_after = client.get("/api/positions").json()
    assert len(positions_after) == 1
    assert positions_after[0]["quantity"] == QUANTITY - 1

    trades_after = client.get("/api/trades").json()
    assert len(trades_after) == 2
    assert [trade["side"] for trade in trades_after] == ["SELL", "BUY"]  # 时间倒序

    # ---------- 7. AI 建议可展示（全链路最后一环） ----------
    advice_response = client.get(f"/api/analysis/{SEED_ZYWOO}")
    assert advice_response.status_code == 200
    _assert_valid_advice(advice_response.json(), SEED_ZYWOO)


@pytest.mark.integration
def test_ai_analysis_always_returns_valid_shape(client, monkeypatch) -> None:
    """无论模型是否可用，AI 接口都必须返回可渲染的结构（source 为 llm 或 rule_fallback）。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    # 调用前后的余额/持仓快照，用于验证"AI 绝不改数据"（TC-205）
    def snapshot() -> tuple[dict, list]:
        return client.get("/api/account").json(), client.get("/api/positions").json()

    before = snapshot()

    # ---------- 1. 模型正常 → source=llm ----------
    def fake_llm(prompt, *, settings=None) -> str:
        return json.dumps(
            {
                "action": "BUY",
                "reason": "当前价 126.0 尚未反映表现分 88，回调后估值偏低",
                "risk_level": "MEDIUM",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(ai.llm_agent, "_default_chat", fake_llm)
    good = client.get(f"/api/analysis/{SEED_ZYWOO}")
    assert good.status_code == 200
    _assert_valid_advice(good.json(), SEED_ZYWOO)
    assert good.json()["source"] == "llm"

    # ---------- 2. 模型超时 → 200 + rule_fallback（不得 4xx/5xx） ----------
    def timeout_llm(prompt, *, settings=None) -> str:
        raise TimeoutError("read timeout=20s")

    monkeypatch.setattr(ai.llm_agent, "_default_chat", timeout_llm)
    fallback = client.get(f"/api/analysis/{SEED_ZYWOO}")
    assert fallback.status_code == 200
    _assert_valid_advice(fallback.json(), SEED_ZYWOO)
    assert fallback.json()["source"] == "rule_fallback"

    # ---------- 3. 选手不存在 → 404（唯一允许的 4xx，且与 AI 故障无关） ----------
    missing = client.get("/api/analysis/999")
    assert missing.status_code == 404
    assert missing.json()["code"] == "PLAYER_NOT_FOUND"

    # ---------- 4. 三次调用（含 404）都没有改动余额/持仓 ----------
    assert snapshot() == before

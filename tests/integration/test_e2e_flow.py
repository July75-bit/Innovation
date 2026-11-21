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

2026-10-24 质量重构：把断言抽成 `_assert_*` / `_get_json` / `_post_json` 辅助函数，
主用例从 63 条语句降到 40 条以内（ruff PLR0915 阈值 50），行为与断言完全不变。
"""

from __future__ import annotations

import json
from typing import Any

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


# ---------------------------------------------------------------- 请求辅助

def _get_json(client: Any, path: str) -> Any:
    """GET 并断言 200，返回解析后的 JSON。"""
    response = client.get(path)
    assert response.status_code == 200, f"GET {path} 返回 {response.status_code}: {response.text}"
    return response.json()


def _post_json(client: Any, path: str, payload: dict) -> dict:
    """POST 并断言 200，返回解析后的 JSON。"""
    response = client.post(path, json=payload)
    assert response.status_code == 200, f"POST {path} 返回 {response.status_code}: {response.text}"
    return response.json()


# ---------------------------------------------------------------- 契约断言

def _assert_valid_advice(body: dict, player_id: int) -> None:
    assert set(body) == ADVICE_KEYS
    assert "suggested_price_band" not in body
    assert body["player_id"] == player_id
    assert body["action"] in VALID_ACTIONS
    assert body["risk_level"] in VALID_RISKS
    assert body["source"] in VALID_SOURCES
    assert 0 < len(body["reason"]) <= 120
    assert body["disclaimer"]


def _assert_market_contract(market: list[dict]) -> dict:
    assert len(market) == 4
    zywoo = next(player for player in market if player["player_id"] == SEED_ZYWOO)
    assert zywoo["name"] == "ZywOo"
    assert zywoo["current_price"] == ZYWOO_PRICE
    assert zywoo["prev_price"] == ZYWOO_PREV_PRICE
    assert zywoo["change_pct"] == 5.0  # (126-120)/120
    assert zywoo["status"] == "trading"
    return zywoo


def _assert_price_history(points: list[dict]) -> None:
    """折线图数据：升序、每点带 reason。"""
    assert len(points) >= 2
    assert all(point["reason"] for point in points)
    assert [point["price"] for point in points] == [ZYWOO_PREV_PRICE, ZYWOO_PRICE]


def _assert_account(
    account: dict,
    *,
    balance: float,
    position_value: float,
    total_asset: float | None = None,
    initial_balance: float | None = None,
) -> None:
    assert account["balance"] == balance
    assert account["position_value"] == position_value
    if total_asset is not None:
        assert account["total_asset"] == total_asset
    if initial_balance is not None:
        assert account["initial_balance"] == initial_balance


def _assert_holding(positions: list[dict], quantity: int) -> None:
    """持仓只剩 ZywOo 一只，数量/均价/市值/浮盈符合契约。"""
    assert len(positions) == 1
    held = positions[0]
    assert held["player_id"] == SEED_ZYWOO
    assert held["quantity"] == quantity
    assert held["avg_cost"] == ZYWOO_PRICE
    assert held["market_value"] == ZYWOO_PRICE * quantity
    assert held["profit"] == 0.0  # 成交价 = 当前价，未涨未跌


def _assert_trades(trades: list[dict], expected_sides: list[str], *, top_quantity: int) -> None:
    """流水按时间倒序，方向序列与最新一笔数量符合预期。"""
    assert [trade["side"] for trade in trades] == expected_sides
    assert all(trade["player_id"] == SEED_ZYWOO for trade in trades)
    assert trades[0]["quantity"] == top_quantity


# ---------------------------------------------------------------- 用例

@pytest.mark.integration
def test_full_trade_flow(client, monkeypatch) -> None:
    """完整交易闭环：查行情 → 买入 → 看持仓 → 卖出 → 余额与流水同步变化。"""
    monkeypatch.setattr(settings, "llm_api_key", "")  # AI 走规则版，测试不碰网络

    # 1. 查行情 + 价格历史
    _assert_market_contract(_get_json(client, "/api/players"))
    _assert_price_history(_get_json(client, f"/api/players/{SEED_ZYWOO}/prices")["points"])

    # 2. 初始账户
    _assert_account(
        _get_json(client, "/api/account"),
        balance=INITIAL_BALANCE,
        position_value=0.0,
        total_asset=INITIAL_BALANCE,
        initial_balance=INITIAL_BALANCE,
    )

    # 3. 买入 2 股
    buy = _post_json(client, "/api/trades/buy", {"player_id": SEED_ZYWOO, "quantity": QUANTITY})
    assert buy["success"] is True
    assert buy["price"] == ZYWOO_PRICE
    assert buy["quantity"] == QUANTITY
    assert buy["balance"] == INITIAL_BALANCE - ZYWOO_PRICE * QUANTITY  # 4748.0

    # 4. 持仓 / 流水出现该笔
    _assert_holding(_get_json(client, "/api/positions"), QUANTITY)
    _assert_trades(_get_json(client, "/api/trades"), ["BUY"], top_quantity=QUANTITY)

    # 5. 卖出 1 股
    sell = _post_json(client, "/api/trades/sell", {"player_id": SEED_ZYWOO, "quantity": 1})
    assert sell["success"] is True
    assert sell["price"] == ZYWOO_PRICE
    assert sell["balance"] == INITIAL_BALANCE - ZYWOO_PRICE * (QUANTITY - 1)  # 4874.0

    # 6. 卖后：余额增加、持仓减少、流水倒序
    _assert_account(
        _get_json(client, "/api/account"),
        balance=4874.0,
        position_value=ZYWOO_PRICE,
        total_asset=5000.0,
    )
    _assert_holding(_get_json(client, "/api/positions"), QUANTITY - 1)
    _assert_trades(_get_json(client, "/api/trades"), ["SELL", "BUY"], top_quantity=1)

    # 7. AI 建议可展示（全链路最后一环）
    _assert_valid_advice(_get_json(client, f"/api/analysis/{SEED_ZYWOO}"), SEED_ZYWOO)


@pytest.mark.integration
def test_ai_analysis_always_returns_valid_shape(client, monkeypatch) -> None:
    """无论模型是否可用，AI 接口都必须返回可渲染的结构（source 为 llm 或 rule_fallback）。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    # 调用前后的余额/持仓快照，用于验证"AI 绝不改数据"（TC-205）
    def snapshot() -> tuple[dict, list]:
        return _get_json(client, "/api/account"), _get_json(client, "/api/positions")

    before = snapshot()

    # 1. 模型正常 → source=llm
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
    good = _get_json(client, f"/api/analysis/{SEED_ZYWOO}")
    _assert_valid_advice(good, SEED_ZYWOO)
    assert good["source"] == "llm"

    # 2. 模型超时 → 200 + rule_fallback（不得 4xx/5xx）
    def timeout_llm(prompt, *, settings=None) -> str:
        raise TimeoutError("read timeout=20s")

    monkeypatch.setattr(ai.llm_agent, "_default_chat", timeout_llm)
    fallback = _get_json(client, f"/api/analysis/{SEED_ZYWOO}")
    _assert_valid_advice(fallback, SEED_ZYWOO)
    assert fallback["source"] == "rule_fallback"

    # 3. 选手不存在 → 404（唯一允许的 4xx，且与 AI 故障无关）
    missing = client.get("/api/analysis/999")
    assert missing.status_code == 404
    assert missing.json()["code"] == "PLAYER_NOT_FOUND"

    # 4. 三次调用（含 404）都没有改动余额/持仓
    assert snapshot() == before

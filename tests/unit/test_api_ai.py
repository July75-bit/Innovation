"""`GET /api/analysis/{player_id}` 接口契约测试（第 3 天由 D 把 AI 模块接进路由）。

负责人：D

守住的契约（`docs/software/api_contract.md` §4.10）：

1. 固定 6 字段：player_id / action / reason / risk_level / source / disclaimer；
   **不含** `suggested_price_band`（可缺省；两版输出一致，规则版不编造区间）；
2. 枚举取值：action ∈ {BUY, SELL, HOLD}，risk_level ∈ {LOW, MEDIUM, HIGH}，
   source ∈ {llm, rule_fallback}；reason ≤ 120 字、disclaimer 非空；
3. 选手不存在 → 404 `PLAYER_NOT_FOUND`；
4. **硬规则**：模型超时 / 异常 / 无密钥一律 200 + `source=rule_fallback`，不得用 4xx/5xx；
5. **只读**（TC-205）：调用前后余额与持仓完全不变。

全部用注入假 `_default_chat` 在无密钥、无网络环境跑通，CI 上不会真的调模型。
"""

from __future__ import annotations

import json

import ai.llm_agent
from app.core.config import settings

SEED_ZYWOO = 1
SEED_UNKNOWN = 999

REQUIRED_KEYS = {
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
    """6 字段 + 枚举 + 长度约束，前端可以无脑渲染。"""
    assert set(body) == REQUIRED_KEYS, f"字段集合不符：{sorted(body)}"
    assert "suggested_price_band" not in body
    assert body["player_id"] == player_id
    assert body["action"] in VALID_ACTIONS
    assert body["risk_level"] in VALID_RISKS
    assert body["source"] in VALID_SOURCES
    assert isinstance(body["reason"], str) and 0 < len(body["reason"]) <= 120
    assert isinstance(body["disclaimer"], str) and body["disclaimer"]


def _snapshot(client) -> tuple[dict, list]:
    """AI 调用前后的账户与持仓快照（TC-205）。"""
    account = client.get("/api/account").json()
    positions = client.get("/api/positions").json()
    return account, positions


def test_analysis_contract_shape_and_rule_fallback(client, monkeypatch):
    """无密钥：200 + 规则版，字段严格是契约里的 6 个。"""
    monkeypatch.setattr(settings, "llm_api_key", "")  # 保证不碰网络

    response = client.get(f"/api/analysis/{SEED_ZYWOO}")

    assert response.status_code == 200
    body = response.json()
    _assert_valid_advice(body, SEED_ZYWOO)
    assert body["source"] == "rule_fallback"
    assert "规则版建议" in body["reason"]


def test_analysis_unknown_player_returns_404(client, monkeypatch):
    """选手不存在返回统一错误体，不是 200，也不是 500。"""
    monkeypatch.setattr(settings, "llm_api_key", "")

    response = client.get(f"/api/analysis/{SEED_UNKNOWN}")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "PLAYER_NOT_FOUND"
    assert body["message"] == "选手不存在"


def test_llm_timeout_still_returns_200_fallback(client, monkeypatch):
    """模型超时不得用 5xx 表达（契约 §4.10 硬规则）。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    def boom(prompt, *, settings=None):
        raise TimeoutError("read timeout=20s")

    monkeypatch.setattr(ai.llm_agent, "_default_chat", boom)

    response = client.get(f"/api/analysis/{SEED_ZYWOO}")

    assert response.status_code == 200
    body = response.json()
    _assert_valid_advice(body, SEED_ZYWOO)
    assert body["source"] == "rule_fallback"


def test_llm_dirty_output_still_returns_200_fallback(client, monkeypatch):
    """模型返回非 JSON / 非法枚举：接口仍是 200 + 规则版（TC-203 接口层）。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")
    monkeypatch.setattr(
        ai.llm_agent, "_default_chat", lambda prompt, *, settings=None: "我觉得可以买入，很强。"
    )

    response = client.get(f"/api/analysis/{SEED_ZYWOO}")

    assert response.status_code == 200
    body = response.json()
    _assert_valid_advice(body, SEED_ZYWOO)
    assert body["source"] == "rule_fallback"


def test_llm_valid_output_is_used(client, monkeypatch):
    """有密钥且模型输出合法：source=llm，action 用模型给的枚举。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    def fake_chat(prompt, *, settings=None):
        return json.dumps(
            {
                "action": "BUY",
                "reason": "当前价 126.0 尚未完全反映表现分 88",
                "risk_level": "MEDIUM",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(ai.llm_agent, "_default_chat", fake_chat)

    response = client.get(f"/api/analysis/{SEED_ZYWOO}")

    assert response.status_code == 200
    body = response.json()
    _assert_valid_advice(body, SEED_ZYWOO)
    assert body["source"] == "llm"
    assert body["action"] == "BUY"
    assert body["risk_level"] == "MEDIUM"


def test_analysis_never_modifies_balance_or_positions(client, monkeypatch):
    """TC-205：AI 只读，调用前后余额/持仓必须完全不变。"""
    monkeypatch.setattr(settings, "llm_api_key", "")

    before = _snapshot(client)
    response = client.get(f"/api/analysis/{SEED_ZYWOO}")
    after = _snapshot(client)

    assert response.status_code == 200
    assert after == before


def test_analysis_does_not_leak_api_key_or_balance_fields(client, monkeypatch):
    """TC-206 的接口层部分：响应里没有密钥，也没有余额/持仓字段。"""
    monkeypatch.setattr(settings, "llm_api_key", "sk-should-not-leak")

    def boom(prompt, *, settings=None):
        raise RuntimeError("测试不真的调模型")

    monkeypatch.setattr(ai.llm_agent, "_default_chat", boom)

    response = client.get(f"/api/analysis/{SEED_ZYWOO}")

    assert response.status_code == 200
    text = response.text
    assert "sk-should-not-leak" not in text
    assert "balance" not in response.json()
    assert "positions" not in response.json()

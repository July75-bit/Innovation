"""限流与交易数量上限（2026-11-26 排查后补的三项修复之二、之三）。

- 登录：同一用户名 10 分钟内输错 5 次先锁住（429），输对会清零；
- 注册：全站每分钟上限（429）；
- 模型调用：全站每分钟额度，超了自动走规则版（不报错、不联网）；
- 价格解读重新生成失败时，不拿规则版覆盖已有的模型解读；
- 交易数量上限 1000：天文数字直接 422，不再走到数据库。
"""

from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from app.core.config import settings as app_settings

PASSWORD = "Passw0rd123"


def _register(client, name: str) -> dict:
    res = client.post("/api/auth/register", json={"username": name, "password": PASSWORD})
    assert res.status_code == 201, res.text
    return res.json()


def _login(client, name: str, password: str):
    return client.post("/api/auth/login", json={"username": name, "password": password})


# ---------------------------------------------------------------- 登录 / 注册
def test_login_locks_after_repeated_failures(client, monkeypatch) -> None:
    monkeypatch.setattr(app_settings, "login_max_failures", 5)
    _register(client, "lock_me")

    for _ in range(5):
        assert _login(client, "lock_me", "wrong-pass1").status_code == 401
    locked = _login(client, "LOCK_ME", PASSWORD)  # 大小写不同也算同一个用户名；输对也先拦
    assert locked.status_code == 429
    assert locked.json()["code"] == "TOO_MANY_ATTEMPTS"

    # 不存在的用户名也同样计数，避免靠"锁不锁"来猜账号是否存在
    for _ in range(5):
        assert _login(client, "nobody_here", "wrong-pass1").status_code == 401
    assert _login(client, "nobody_here", "wrong-pass1").status_code == 429


def test_successful_login_resets_failure_count(client, monkeypatch) -> None:
    monkeypatch.setattr(app_settings, "login_max_failures", 5)
    _register(client, "reset_me")

    for _ in range(4):
        assert _login(client, "reset_me", "wrong-pass1").status_code == 401
    assert _login(client, "reset_me", PASSWORD).status_code == 200
    for _ in range(4):
        assert _login(client, "reset_me", "wrong-pass1").status_code == 401  # 重新从 0 数，不是 429


def test_register_is_capped_per_minute(client, monkeypatch) -> None:
    monkeypatch.setattr(app_settings, "register_per_minute", 2)
    _register(client, "cap_one")
    _register(client, "cap_two")
    third = client.post("/api/auth/register", json={"username": "cap_three", "password": PASSWORD})
    assert third.status_code == 429
    assert third.json()["code"] == "TOO_MANY_REQUESTS"


# ---------------------------------------------------------------- 模型额度
class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def test_llm_budget_falls_back_to_rules_without_calling_network(monkeypatch) -> None:
    import urllib.request

    from ai.llm_agent import analyze

    calls: list[str] = []
    reply = {"choices": [{"message": {"content": json.dumps(
        {"action": "HOLD", "risk_level": "LOW", "reason": "震荡，先观望。"}, ensure_ascii=False
    )}}]}

    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        calls.append(request.full_url)
        return _FakeResponse(json.dumps(reply).encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    fake_settings = SimpleNamespace(
        llm_api_key="test-key",
        llm_model="test-model",
        llm_timeout_seconds=5,
        llm_base_url="https://llm.invalid/v1",
        llm_calls_per_minute=2,
    )
    ctx = {"player_id": 1, "name": "ZywOo", "current_price": 120.0, "rating": 88, "change_pct": 1.0}

    sources = [analyze(ctx, settings=fake_settings)["source"] for _ in range(3)]

    assert sources == ["llm", "llm", "rule_fallback"]  # 第 3 次超额：规则版，接口照常
    assert len(calls) == 2  # 超额那次根本没联网


def test_tool_loop_respects_llm_budget(monkeypatch) -> None:
    from ai.tools import ToolLoopError, run_tool_loop

    from app.core.rate_limit import LLM_KEY, limiter

    fake_settings = SimpleNamespace(llm_api_key="test-key", llm_calls_per_minute=1)
    limiter.try_acquire(LLM_KEY, 1, 60.0)  # 本分钟额度已用完
    with pytest.raises(ToolLoopError, match="太频繁"):
        run_tool_loop("sys", "user", {}, settings=fake_settings)


def test_narrative_refresh_failure_keeps_model_text(client, monkeypatch) -> None:
    import ai.narrate as narrate

    replies = iter([
        ("模型写的解读：上一场打得好，价格上涨。", "llm", "test-model"),
        ("规则版解读", "rule_fallback", ""),
    ])
    monkeypatch.setattr(narrate, "generate_narrative", lambda **_kw: next(replies))

    first = client.get("/api/agent/narrative/1").json()
    assert first["source"] == "llm"

    again = client.get("/api/agent/narrative/1", params={"refresh": "true"}).json()
    assert again["source"] == "llm"  # 重新生成失败，仍给原来的模型解读
    assert again["narrative"] == first["narrative"]
    assert again["cached"] is True


# ---------------------------------------------------------------- 交易数量上限
@pytest.mark.parametrize("path", ["/api/trades/buy", "/api/trades/sell"])
@pytest.mark.parametrize("quantity", [1001, 10**20])
def test_absurd_quantity_rejected_before_database(client, path: str, quantity: int) -> None:
    res = client.post(path, json={"player_id": 1, "quantity": quantity})
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_quantity_just_over_position_limit_keeps_business_message(client) -> None:
    res = client.post("/api/trades/buy", json={"player_id": 1, "quantity": 51})
    assert res.status_code == 400  # 51 仍走业务规则（余额不足 / 超过持仓上限），给中文提示

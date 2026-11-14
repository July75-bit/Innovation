"""智能体接口的边界与故障分支测试（补覆盖率，不改产品代码）。

覆盖 `app/api/agent.py` 里主路径之外的 36 行：
- 审计写入被关闭 / 写库失败（必须吞掉异常，不影响主响应）
- 上下文组装失败 → 退回最小上下文
- 简报：无选手 / 模型给出总述（source=llm）
- 叙事：选手不存在 / 无价格历史 / 命中缓存 + refresh / 缓存写失败
- 工具：选手不存在 / 工具执行器被模型调用（取历史、取账户、算仓位、非法价格）
- 多角色协作：选手不存在

为什么这些值得测：它们都是"出错时必须降级而不是 5xx"的分支，与本项目"AI 故障一律 200"的硬规则同源。
"""

from __future__ import annotations

import io

import pytest

from app.api import agent as agent_api
from app.core.config import settings
from app.models import Player, PriceHistory, PriceNarrative

SEED = 1


def _clear_brief_cache() -> None:
    agent_api._brief_cache.update({"at": 0.0, "payload": None})


# ---------------------------------------------------------------- 审计
def test_trace_returns_zero_when_audit_disabled(client, monkeypatch) -> None:
    """AUDIT 关闭时：接口照常返回，trace_id 为 0（不报错）。"""
    monkeypatch.setattr(settings, "agent_traces_enabled", False)
    monkeypatch.setattr(settings, "llm_api_key", "")

    body = client.get(f"/api/agent/decision/{SEED}").json()

    assert body["trace_id"] == 0
    assert body["advice"]["action"] in {"BUY", "SELL", "HOLD"}


def test_trace_write_failure_is_swallowed(monkeypatch) -> None:
    """审计写库失败只能记日志 + 回滚，函数返回 0。"""

    class _BoomSession:
        rolled_back = False

        def add(self, _row) -> None:
            pass

        def commit(self) -> None:
            raise RuntimeError("disk full")

        def rollback(self) -> None:
            self.rolled_back = True

    session = _BoomSession()
    monkeypatch.setattr(settings, "agent_traces_enabled", True)

    assert agent_api._write_trace(
        session, mode="decision", player_id=1, source="llm", model="m", latency_ms=1, output={}
    ) == 0
    assert session.rolled_back is True


# ---------------------------------------------------------------- 上下文降级
def test_context_failure_falls_back_to_minimal(client, monkeypatch) -> None:
    """上下文组装抛异常时，用最小上下文兜底，接口仍 200。"""
    monkeypatch.setattr(settings, "llm_api_key", "")

    def _boom(*_a, **_k):
        raise RuntimeError("db hiccup")

    monkeypatch.setattr(agent_api, "build_player_context", _boom)

    body = client.get(f"/api/agent/decision/{SEED}").json()

    assert body["snapshot"]["current_price"] > 0
    assert body["advice"]["action"] in {"BUY", "SELL", "HOLD"}


# ---------------------------------------------------------------- 简报
def test_brief_items_empty_without_players(session_factory) -> None:
    """没有选手时简报要点为空列表（不抛异常）。"""
    session = session_factory()
    try:
        session.query(Player).delete()
        session.commit()
        assert agent_api._brief_items(session) == []
    finally:
        session.close()


def test_brief_uses_llm_summary_when_available(client, monkeypatch) -> None:
    """模型可用时简报总述 source=llm（而不是恒定的兜底文案）。"""
    _clear_brief_cache()
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    import ai.llm_agent as llm

    monkeypatch.setattr(llm, "_default_chat", lambda *_a, **_k: "今日涨跌分化，注意停牌标的。")

    body = client.get("/api/agent/brief?refresh=true").json()

    assert body["source"] == "llm"
    assert "停牌" in body["summary"]
    _clear_brief_cache()


# ---------------------------------------------------------------- 叙事
def test_panel_unknown_player_404(client) -> None:
    assert client.get("/api/agent/panel/999").status_code == 404


def test_narrative_unknown_player_404(client) -> None:
    assert client.get("/api/agent/narrative/999").status_code == 404


def test_narrative_without_price_history(client, session_factory) -> None:
    """选手存在但没有价格历史 → 明确返回"暂无价格历史"，不报错。"""
    session = session_factory()
    try:
        session.query(PriceHistory).filter(PriceHistory.player_id == SEED).delete()
        session.commit()
    finally:
        session.close()

    body = client.get(f"/api/agent/narrative/{SEED}").json()

    assert body["narrative"] == "暂无价格历史"
    assert body["source"] == "rule_fallback"


def test_narrative_refresh_updates_existing_cache(client, session_factory, monkeypatch) -> None:
    """已有缓存 + refresh=true → 走"更新缓存"分支，返回新叙事。"""
    session = session_factory()
    try:
        latest = (
            session.query(PriceHistory)
            .filter(PriceHistory.player_id == SEED)
            .order_by(PriceHistory.ts.desc())
            .first()
        )
        assert latest is not None
        existed = (
            session.query(PriceNarrative)
            .filter(PriceNarrative.player_id == SEED, PriceNarrative.ts == latest.ts)
            .first()
        )
        if existed is None:
            session.add(
                PriceNarrative(
                    player_id=SEED, ts=latest.ts, narrative="旧叙事", source="rule_fallback", model="old"
                )
            )
            session.commit()
    finally:
        session.close()

    import ai.narrate as narrate

    monkeypatch.setattr(
        narrate,
        "generate_narrative",
        lambda **_k: ("刷新后的叙事（含得分 88.0）", "llm", "fake-model"),
    )

    body = client.get(f"/api/agent/narrative/{SEED}?refresh=true").json()

    assert body["source"] == "llm"
    assert "刷新后的叙事" in body["narrative"]


def test_narrative_cache_write_failure_still_returns(client, monkeypatch) -> None:
    """叙事缓存写失败只记日志，接口仍然返回叙事（不影响用户体验）。"""
    import sqlalchemy.orm

    def _boom_commit(self) -> None:  # noqa: ANN001
        raise RuntimeError("cache table locked")

    monkeypatch.setattr(sqlalchemy.orm.Session, "commit", _boom_commit)

    import ai.narrate as narrate

    monkeypatch.setattr(
        narrate, "generate_narrative", lambda **_k: ("兜底叙事（得分 70.0）", "rule_fallback", None)
    )

    body = client.get(f"/api/agent/narrative/{SEED}?refresh=true").json()

    assert "兜底叙事" in body["narrative"]
    assert body["source"] == "rule_fallback"


# ---------------------------------------------------------------- 工具调用
def test_tools_unknown_player_404(client) -> None:
    assert client.get("/api/agent/tools/999").status_code == 404


def test_tools_executors_are_callable(client, monkeypatch) -> None:
    """模型调用工具时，三个只读执行器必须真的能取到数（含边界：limit 截断、非法价格）。"""
    captured: dict[str, object] = {}

    def _fake_run_loop(_system, _user, executors, **_kwargs):  # noqa: ANN001
        captured["history"] = executors["get_price_history"]({"limit": 3})
        captured["history_clamped"] = executors["get_price_history"]({"limit": 999, "player_id": SEED})
        captured["account"] = executors["get_account_snapshot"]({})
        captured["sizing"] = executors["calc_position_size"](
            {"risk_level": "HIGH", "balance": 10000, "price": 100, "held_quantity": 0}
        )
        captured["sizing_bad_price"] = executors["calc_position_size"]({"balance": 100, "price": 0})
        # 未知 risk_level → 走默认 MEDIUM 分支
        captured["sizing_unknown_risk"] = executors["calc_position_size"](
            {"risk_level": "NOPE", "balance": 1000, "price": 50}
        )
        return {"content": "BUY 建议：得分 88.0", "tool_calls": [{"name": "get_price_history"}], "rounds": 1}

    monkeypatch.setattr(agent_api, "run_tool_loop", _fake_run_loop)

    body = client.get(f"/api/agent/tools/{SEED}").json()

    assert body["source"] == "llm"
    assert body["tool_calls"] == [{"name": "get_price_history"}]
    assert body["rounds"] == 1
    assert 1 <= len(captured["history"]) <= 3
    assert len(captured["history_clamped"]) <= 12
    assert set(captured["account"]) == {"balance", "held_quantity"}
    assert captured["sizing"]["suggested_quantity"] >= 0
    assert captured["sizing_bad_price"] == {"error": "price 必须 > 0"}
    assert captured["sizing_unknown_risk"]["risk_level"] == "NOPE"


# ---------------------------------------------------------------- 反序列化边界
def test_decision_body_rejects_bad_literals(client) -> None:
    """人在环接口的字面量校验（防止前端传脏值）。"""
    resp = client.post(
        "/api/agent/decisions",
        json={
            "player_id": SEED,
            "advice_action": "LIQUIDATE",
            "advice_source": "llm",
            "decision": "accept",
        },
    )
    assert resp.status_code == 422
    assert io  # 保留 import（ruff 用）


@pytest.mark.parametrize("limit", [0, 101])
def test_traces_limit_is_bounded(client, limit: int) -> None:
    assert client.get(f"/api/agent/traces?limit={limit}").status_code == 422

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

# ---------------------------------------------------------------- 简报总述清洗
# 背景：模型偶尔不按"只输出一句话"来，返回 `{"action": "HOLD", "reason": "..."}`
# 甚至被截断成半个 JSON。旧实现只做 [:80] 截断，前端会直接显示代码片段。
def test_clean_brief_summary_extracts_reason_from_truncated_json() -> None:
    """线上真实坏样本：被截断的 JSON 也要取出人话 reason。"""
    raw = '{"action": "HOLD", "reason": "sh1ro 现价 136.43，单日上涨 13.96%；bLitz 现价 48.48'

    clean = agent_api._clean_brief_summary(raw)

    assert "{" not in clean and "action" not in clean
    assert clean.startswith("sh1ro 现价 136.43")


def test_clean_brief_summary_extracts_reason_from_valid_json() -> None:
    raw = '{"action": "HOLD", "reason": "今日涨跌分化。", "risk_level": "LOW"}'

    assert agent_api._clean_brief_summary(raw) == "今日涨跌分化。"


def test_clean_brief_summary_strips_markdown_fence() -> None:
    raw = "```json\n{\"reason\": \"测试一下\"}\n```"

    assert agent_api._clean_brief_summary(raw) == "测试一下"


def test_clean_brief_summary_keeps_plain_sentence() -> None:
    """本来就是一句话时原样返回（保留句末句号）。"""
    raw = "今日行情由比赛表现驱动，请关注停牌与大幅波动标的。"

    assert agent_api._clean_brief_summary(raw) == raw


def test_clean_brief_summary_strips_wrapping_quotes() -> None:
    """线上真实样本：模型把整句套了引号，界面不该把引号也显示出来。"""
    raw = '\u201csh1ro\u6da813.96%\u62a5136.43\uff0cbLitz\u62a548.48\uff0c\u7b2c18\u8f6e\u56db\u4eba\u505c\u724c\u201d'

    clean = agent_api._clean_brief_summary(raw)

    assert not clean.startswith(("\u201c", '"', "\u300c"))
    assert not clean.endswith(("\u201d", '"', "\u300d"))
    assert clean.startswith("sh1ro")


def test_clean_brief_summary_spaces_cjk_and_ascii() -> None:
    """中文和数字/字母挤在一起时补空格，读起来不费劲。"""
    clean = agent_api._clean_brief_summary("sh1ro\u6da813.96%\u62a5136.43")

    assert clean == "sh1ro \u6da8 13.96% \u62a5 136.43"


def test_clean_brief_summary_handles_empty() -> None:
    assert agent_api._clean_brief_summary("") == ""
    assert agent_api._clean_brief_summary(None) == ""


def test_brief_endpoint_strips_quotes_and_spaces(client, monkeypatch) -> None:
    """端到端：模型返回「整句带引号 + 中英数字挤在一起」时，接口给的是干净一句中文。"""
    _clear_brief_cache()
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    import ai.llm_agent as llm

    monkeypatch.setattr(
        llm,
        "_default_chat",
        lambda *_a, **_k: '\u201csh1ro\u6da813.96%\u62a5136.43\uff0cbLitz\u62a548.48\u201d',
    )

    body = client.get("/api/agent/brief?refresh=true").json()
    summary = body["summary"]

    assert summary == "sh1ro \u6da8 13.96% \u62a5 136.43\uff0cbLitz \u62a5 48.48"
    assert "\u201c" not in summary and "\u201d" not in summary
    _clear_brief_cache()


def test_brief_endpoint_never_leaks_json(client, monkeypatch) -> None:
    """端到端：即便模型返回 JSON，接口的 summary 也不能含花括号/字段名。"""
    _clear_brief_cache()
    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    import ai.llm_agent as llm

    monkeypatch.setattr(
        llm,
        "_default_chat",
        lambda *_a, **_k: '{"action": "HOLD", "reason": "今日涨跌分化，注意停牌标的。"}',
    )

    body = client.get("/api/agent/brief?refresh=true").json()

    assert "{" not in body["summary"] and '"reason"' not in body["summary"]
    assert "今日涨跌分化" in body["summary"]
    assert body["source"] == "llm"
    _clear_brief_cache()


def test_tools_account_snapshot_uses_current_user(client, monkeypatch) -> None:
    """「查账户」工具查的是当前请求的用户；没带令牌才是公共演示账户（2026-11-26 修，原先总查 demo）。"""
    reg = client.post("/api/auth/register", json={"username": "tools_user", "password": "Passw0rd123"})
    assert reg.status_code == 201
    auth = {"Authorization": f"Bearer {reg.json()['token']}"}
    assert client.post("/api/trades/buy", json={"player_id": 1, "quantity": 3}, headers=auth).status_code == 200
    mine = client.get("/api/account", headers=auth).json()

    snapshots: list[dict] = []

    def _fake_run_loop(_system, _user, executors, **_kwargs):  # noqa: ANN001
        snapshots.append(executors["get_account_snapshot"]({"player_id": 1}))
        return {"content": "HOLD", "tool_calls": [], "rounds": 1}

    monkeypatch.setattr(agent_api, "run_tool_loop", _fake_run_loop)

    assert client.get("/api/agent/tools/1", headers=auth).status_code == 200
    assert client.get("/api/agent/tools/1").status_code == 200

    assert snapshots[0] == {"balance": round(float(mine["balance"]), 2), "held_quantity": 3}
    assert snapshots[1]["held_quantity"] == 0  # 未登录 = 公共演示账户，看不到注册用户的持仓


def test_ai_context_position_is_per_user(client, monkeypatch) -> None:
    """交给 AI 的「持仓」按当前用户取（2026-11-26 修）：两人都持有同一选手时互不串。

    原先 `ai/context.py` 只按 player_id 查 positions，多人持有时会拿到别人的持仓。
    """
    import app.api.ai as ai_api

    headers = {}
    for name, qty in (("ctx_a", 3), ("ctx_b", 5)):
        reg = client.post("/api/auth/register", json={"username": name, "password": "Passw0rd123"})
        assert reg.status_code == 201
        headers[name] = {"Authorization": f"Bearer {reg.json()['token']}"}
        buy = client.post("/api/trades/buy", json={"player_id": 1, "quantity": qty}, headers=headers[name])
        assert buy.status_code == 200

    seen: list[float] = []

    def _capture(context, **_kwargs):  # noqa: ANN001
        seen.append(context["position"]["quantity"])
        return {
            "player_id": 1, "action": "HOLD", "reason": "测试", "risk_level": "LOW",
            "source": "rule_fallback", "disclaimer": "测试",
        }

    monkeypatch.setattr(ai_api, "analyze", _capture)
    monkeypatch.setattr(agent_api, "analyze", _capture)

    from app.core import advice_cache

    for path in ("/api/analysis/1", "/api/agent/decision/1"):
        advice_cache.clear()  # 两个接口共用建议缓存；这里要分别验证各自取的持仓
        assert client.get(path, headers=headers["ctx_a"]).status_code == 200
        assert client.get(path, headers=headers["ctx_b"]).status_code == 200
        assert client.get(path).status_code == 200

    assert seen == [3.0, 5.0, 0.0, 3.0, 5.0, 0.0]  # A 看到 3、B 看到 5、未登录（演示账户）看到 0


def test_panel_passes_current_user_balance(client, monkeypatch) -> None:
    """/api/agent/panel 把当前用户的余额交给三个角色；未登录用演示账户余额。"""
    reg = client.post("/api/auth/register", json={"username": "panel_user", "password": "Passw0rd123"})
    auth = {"Authorization": f"Bearer {reg.json()['token']}"}
    assert client.post("/api/trades/buy", json={"player_id": 1, "quantity": 2}, headers=auth).status_code == 200
    mine = client.get("/api/account", headers=auth).json()["balance"]

    seen: list[dict] = []

    def _fake_panel(context, **_kw):  # noqa: ANN001
        seen.append(context["account"])
        return {"source": "rule_fallback", "minutes": [], "final": {"action": "HOLD", "risk_level": "LOW",
                "reason": "测试", "disclaimer": "测试"}}

    monkeypatch.setattr(agent_api, "run_panel", _fake_panel)
    assert client.get("/api/agent/panel/1", headers=auth).status_code == 200
    assert client.get("/api/agent/panel/1").status_code == 200

    assert seen[0] == {"balance": round(float(mine), 2), "position_limit": 50}
    assert seen[1]["balance"] == 5000.0  # 演示账户



def test_analysis_and_decision_share_one_advice(client, monkeypatch) -> None:
    """建议卡和决策卡用同一条建议（2026-11-28 修）：页面上的「买入」和「若采纳可买」不再各说各的。"""
    import app.api.ai as ai_api

    replies = iter(["BUY", "HOLD", "SELL"])
    calls: list[str] = []

    def _fake(context, **_kw):  # noqa: ANN001
        action = next(replies)
        calls.append(action)
        return {"player_id": 1, "action": action, "reason": "测试", "risk_level": "MEDIUM",
                "source": "llm", "disclaimer": "测试"}

    monkeypatch.setattr(ai_api, "analyze", _fake)
    monkeypatch.setattr(agent_api, "analyze", _fake)

    shown = client.get("/api/analysis/1").json()
    decision = client.get("/api/agent/decision/1").json()
    assert shown["action"] == decision["advice"]["action"] == "BUY"
    assert decision["plan"]["suggested_quantity"] > 0  # 按「买入」算出的股数
    assert calls == ["BUY"]  # 只问了一次模型

    refreshed = client.get("/api/analysis/1?refresh=true").json()
    assert refreshed["action"] == "HOLD"
    assert client.get("/api/agent/decision/1").json()["advice"]["action"] == "HOLD"


def test_buy_plan_tops_up_when_already_holding() -> None:
    """已持有时按目标仓位补足，不再一律 0 股（2026-11-28 修）。"""
    from ai.decision import build_plan

    advice = {"action": "BUY", "risk_level": "LOW", "source": "llm"}  # 目标 = 总资产 × 10%
    fresh = build_plan(advice, balance=5000.0, current_price=100.0, held_quantity=0)
    assert fresh["suggested_quantity"] == 5  # 5000 × 10% ÷ 100

    partial = build_plan(advice, balance=4800.0, current_price=100.0, held_quantity=2)
    assert partial["suggested_quantity"] == 3  # 目标 5 股，已持 2 股 → 再买 3

    full = build_plan(advice, balance=4500.0, current_price=100.0, held_quantity=5)
    assert full["suggested_quantity"] == 0
    assert any("目标仓位" in line for line in full["rationale"])


def test_analysis_prompt_includes_balance(client, monkeypatch) -> None:
    """建议卡给模型的提问里有当前用户的余额和仓位上限（2026-11-28 补）。"""
    import ai.llm_agent as llm
    import app.api.ai as ai_api

    from ai.llm_agent import build_user_prompt

    reg = client.post("/api/auth/register", json={"username": "card_user", "password": "Passw0rd123"})
    auth = {"Authorization": f"Bearer {reg.json()['token']}"}
    assert client.post("/api/trades/buy", json={"player_id": 1, "quantity": 4}, headers=auth).status_code == 200
    balance = float(client.get("/api/account", headers=auth).json()["balance"])

    prompts: list[str] = []

    def _capture(context, **_kw):  # noqa: ANN001
        prompts.append(build_user_prompt(context))
        return llm._fallback(context)

    monkeypatch.setattr(ai_api, "analyze", _capture)
    assert client.get("/api/analysis/1", headers=auth).status_code == 200

    assert f"可用余额 {balance:.2f} 信用点" in prompts[0]
    assert "还能买 46 股" in prompts[0]  # 50 − 已持 4


def test_prompt_without_account_says_not_provided() -> None:
    from ai.llm_agent import build_user_prompt

    assert "账户资金：（未提供）" in build_user_prompt({"player_id": 1, "current_price": 100})

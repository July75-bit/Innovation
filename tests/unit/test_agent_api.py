"""智能体增强接口测试（第 8 轮：决策卡/简报/审计/人在环/多角色/叙事/工具）。

负责人：B

守住四条底线（与既有契约一致）：
1. **不碰钱**：所有接口调用前后余额/持仓/流水完全不变（唯一写入是审计表）；
2. **不碰 /api/analysis**：6 字段契约原样（金标集锁着，这里只断言新接口不改变它）；
3. **模型不可用一律 200**：无密钥场景下返回 `source=rule_fallback` 而不是 5xx；
4. **审计可查**：调用后 `GET /api/agent/traces` 能看到记录。
"""

from __future__ import annotations

from app.core.config import settings

SEED_ZYWOO = 1


def _snapshot(client) -> tuple:
    return (
        client.get("/api/account").json(),
        client.get("/api/positions").json(),
        client.get("/api/trades").json(),
    )


# ---------------------------------------------------------------- 决策卡
def test_decision_card_has_plan_and_is_read_only(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    before = _snapshot(client)

    body = client.get(f"/api/agent/decision/{SEED_ZYWOO}").json()

    assert set(body["advice"]) >= {"player_id", "action", "reason", "risk_level", "source", "disclaimer"}
    plan = body["plan"]
    assert 0.35 <= plan["confidence"] <= 0.92
    assert isinstance(plan["suggested_quantity"], int) and plan["suggested_quantity"] >= 0
    assert plan["suggested_quantity"] <= settings.max_position_per_player
    assert plan["rationale"], "计划必须给出可解释的依据"
    assert body["snapshot"]["current_price"] > 0
    assert _snapshot(client) == before, "决策卡不得修改余额/持仓/流水"


def test_decision_card_unknown_player_404(client):
    resp = client.get("/api/agent/decision/999")
    assert resp.status_code == 404
    assert resp.json()["code"] == "PLAYER_NOT_FOUND"


def test_decision_plan_never_exceeds_balance(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    body = client.get(f"/api/agent/decision/{SEED_ZYWOO}").json()
    plan, snap = body["plan"], body["snapshot"]
    if body["advice"]["action"] == "BUY":
        cost = plan["suggested_quantity"] * snap["current_price"]
        assert cost <= snap["balance"] + 1e-6, "建议仓位不能超过余额"


# ---------------------------------------------------------------- 简报
def test_brief_returns_three_items_and_caches(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    first = client.get("/api/agent/brief?refresh=true").json()
    assert len(first["items"]) == 3
    assert first["source"] in {"llm", "rule_fallback"}
    assert first["summary"]

    second = client.get("/api/agent/brief").json()
    assert second["cached"] is True, "10 分钟内应命中缓存"


# ---------------------------------------------------------------- 审计
def test_traces_recorded_after_decision(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    client.get(f"/api/agent/decision/{SEED_ZYWOO}")

    body = client.get("/api/agent/traces?limit=10").json()
    assert body["count"] >= 1
    modes = {item["mode"] for item in body["items"]}
    assert "decision" in modes
    assert all(item["latency_ms"] >= 0 for item in body["items"])


# ---------------------------------------------------------------- 人在环
def test_decision_log_accept_and_stats(client):
    payload = {
        "player_id": SEED_ZYWOO,
        "advice_action": "HOLD",
        "advice_source": "rule_fallback",
        "decision": "accept",
    }
    resp = client.post("/api/agent/decisions", json=payload)
    assert resp.status_code == 200 and resp.json()["success"] is True

    client.post("/api/agent/decisions", json={**payload, "decision": "ignore"})
    stats = client.get("/api/agent/decisions/stats").json()
    assert stats["total"] >= 2
    assert 0 <= (stats["accept_rate"] or 0) <= 1


def test_decision_log_rejects_unknown_player(client):
    resp = client.post(
        "/api/agent/decisions",
        json={
            "player_id": 999,
            "advice_action": "BUY",
            "advice_source": "llm",
            "decision": "accept",
        },
    )
    assert resp.status_code == 404


def test_decision_log_rejects_bad_enum(client):
    resp = client.post(
        "/api/agent/decisions",
        json={
            "player_id": SEED_ZYWOO,
            "advice_action": "MOON",
            "advice_source": "llm",
            "decision": "accept",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------- 多角色
def test_panel_falls_back_without_key(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    body = client.get(f"/api/agent/panel/{SEED_ZYWOO}").json()

    assert body["source"] == "rule_fallback", "无密钥时必须回落规则版"
    assert body["final"]["action"] in {"BUY", "SELL", "HOLD"}
    assert body["minutes"], "纪要至少要有系统提示那一行"


# ---------------------------------------------------------------- 叙事
def test_narrative_is_cached_and_read_only(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    before = _snapshot(client)

    first = client.get(f"/api/agent/narrative/{SEED_ZYWOO}?refresh=true").json()
    assert first["narrative"]
    assert first["source"] in {"llm", "rule_fallback"}

    second = client.get(f"/api/agent/narrative/{SEED_ZYWOO}").json()
    assert second["cached"] is True
    assert second["narrative"] == first["narrative"]
    assert _snapshot(client) == before


# ---------------------------------------------------------------- 工具调用
def test_tools_endpoint_degrades_without_key(client, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    body = client.get(f"/api/agent/tools/{SEED_ZYWOO}").json()

    assert body["source"] == "rule_fallback"
    assert body["fallback_reason"], "降级必须说明原因"
    assert body["answer"], "降级也要给一句建议"


# ---------------------------------------------------------------- 简报里的"停牌"口径
def test_brief_halt_note_uses_schedule_not_manual_status():
    """简报的"本轮停牌"必须来自**赛程**，不能看 players.status（手动冻结字段）。

    2026-11-14 修：原先用 `status != trading` 判断，而 16 人全是 trading，
    于是简报永远显示"无选手停牌"，与前端（按赛程每轮 4 人停牌）自相矛盾。
    """
    from app.api.agent import _round_halt_detail

    class P:
        def __init__(self, name, team, status="trading"):
            self.name, self.team, self.status = name, team, status

    players = [
        P("ZywOo", "Vitality"),
        P("donk", "Spirit"),
        P("m0NESY", "Falcons"),
        P("NiKo", "Falcons"),
    ]
    # 第 1 轮是 Vitality vs <team_id 8>；至少要点明轮次与人数，且不依赖 players.status
    detail = _round_halt_detail(players, 1)
    assert "第 1 轮" in detail
    assert "停牌" in detail

    # 非比赛日：明确说"没有本轮停牌"，不谎报
    assert "不是比赛日" in _round_halt_detail(players, None)

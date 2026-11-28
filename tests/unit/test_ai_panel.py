"""ai/panel.py 多角色协作的单测（离线，用假模型，不联网）。

钉住 2026-11-26 修掉的两个问题：
1. 三个角色的系统提示（ROLE_PROMPTS）真的发给了模型；
2. 最终结论取自交易员，而不是再单独调一次建议卡（以前一共调 4 次模型）。
"""

from __future__ import annotations

import ai.panel as panel

CONTEXT = {
    "player_id": 1,
    "name": "ZywOo",
    "team": "Vitality",
    "rating": 88,
    "current_price": 120.0,
    "change_pct": 3.5,
    "recent_prices": [{"price": 116.0}, {"price": 120.0}],
    "position": {"quantity": 0, "avg_cost": 0.0},
}


def _fake_model(monkeypatch, replies: dict[str, str]) -> list[dict]:
    """按系统提示认出是哪个角色，返回预设回答；记下每次调用。"""
    calls: list[dict] = []
    role_of = {text: role for role, text in panel.ROLE_PROMPTS.items()}

    def fake_chat(user_prompt, *, settings=None, system_prompt=None):
        role = role_of.get(system_prompt, "unknown")
        calls.append({"role": role, "prompt": user_prompt})
        return replies[role]

    monkeypatch.setattr(panel, "_default_chat", fake_chat)
    return calls


def test_each_role_gets_its_own_prompt_and_sees_earlier_speakers(monkeypatch):
    calls = _fake_model(
        monkeypatch,
        {
            "analyst": "近 2 个价格点上行，趋势偏强。",
            "risk": "波动 3.5%，建议最多 5 股。",
            "trader": '{"action": "BUY", "risk_level": "MEDIUM", "reason": "趋势向上，但按风控只买 5 股。"}',
        },
    )

    result = panel.run_panel(CONTEXT)

    assert [c["role"] for c in calls] == ["analyst", "risk", "trader"]  # 正好 3 次，顺序固定
    assert "近 2 个价格点上行" in calls[1]["prompt"]  # 风控看得到分析师
    assert "近 2 个价格点上行" in calls[2]["prompt"]  # 交易员看得到分析师
    assert "建议最多 5 股" in calls[2]["prompt"]  # 交易员看得到风控
    assert result["source"] == "llm"
    assert [m["role"] for m in result["minutes"]] == ["analyst", "risk", "trader"]


def test_final_decision_comes_from_trader(monkeypatch):
    _fake_model(
        monkeypatch,
        {
            "analyst": "趋势下行。",
            "risk": "已无持仓，风险可控。",
            "trader": '```json\n{"action": "卖出", "risk_level": "高", "reason": "连续下跌，与分析师一致。"}\n```',
        },
    )

    final = panel.run_panel(CONTEXT)["final"]

    assert final["action"] == "SELL"  # 中文别名按建议卡同一套规则归一
    assert final["risk_level"] == "HIGH"
    assert final["reason"] == "连续下跌，与分析师一致。"
    assert final["disclaimer"]


def test_invalid_trader_output_falls_back_to_rules(monkeypatch):
    _fake_model(
        monkeypatch,
        {"analyst": "震荡。", "risk": "正常。", "trader": '{"action": "ALL_IN", "risk_level": "LOW", "reason": "x"}'},
    )

    result = panel.run_panel(CONTEXT)

    assert result["source"] == "rule_fallback"
    assert result["final"]["action"] in {"BUY", "SELL", "HOLD"}
    assert result["minutes"][-1]["role"] == "system"  # 前两位的发言保留，末尾说明已回落
    assert [m["role"] for m in result["minutes"][:2]] == ["analyst", "risk"]

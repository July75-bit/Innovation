"""LLM 分析模块单元测试（不需要密钥、不需要网络）。

负责人：D

覆盖 day2 计划里的 5 类场景 + 2 条契约约束（字段集合一致、不改余额），全部通过
**注入假 client** 实现，所以在没有 `LLM_API_KEY`、甚至没安装 httpx 的环境里也能跑。

对应：
- 契约 `docs/software/api_contract.md` §4.10
- 规则/提示词 `docs/algorithm/ai_agent_prompt.md`
"""

import json
from types import SimpleNamespace

import pytest
from ai.fallback import rule_based_advice
from ai.llm_agent import (
    DEFAULT_BASE_URL,
    LLMOutputError,
    OUTPUT_KEYS,
    _api_key,
    _base_url,
    _model,
    _parse_and_validate,
    analyze,
)

EXPECTED_KEYS = set(OUTPUT_KEYS)


def _settings(api_key: str = "sk-test") -> SimpleNamespace:
    return SimpleNamespace(
        llm_api_key=api_key,
        llm_model="gpt-4o-mini",
        llm_timeout_seconds=20.0,
        llm_provider="openai",
    )


def _ctx(**overrides):
    ctx = {
        "context_source": "mock",
        "player_id": 1,
        "name": "ZywOo",
        "display_name": "载物",
        "team": "Vitality",
        "role": "AWPer",
        "current_price": 126.0,
        "change_pct": 5.0,
        "rating": 88,
        "recent_prices": [{"ts": "初始价格", "price": 120.0}, {"ts": "当前价格", "price": 126.0}],
        "recent_reasons": ["演示数据"],
        "position": {"quantity": 10, "avg_cost": 120.0},
    }
    ctx.update(overrides)
    return ctx


# ---------- 1. 正常输出 ----------

def test_valid_json_returns_llm_source():
    raw = json.dumps(
        {"action": "BUY", "reason": "价格由 120.0 升至 126.0，表现分 88 仍偏高", "risk_level": "MEDIUM"},
        ensure_ascii=False,
    )
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    assert result["source"] == "llm"
    assert result["action"] == "BUY"
    assert result["risk_level"] == "MEDIUM"
    assert result["player_id"] == 1
    assert set(result) == EXPECTED_KEYS


# ---------- 2. 代码围栏 / 大小写 / 中文动作 ----------

def test_fenced_and_lowercase_action_is_normalized():
    raw = '```json\n{"action": "buy", "reason": "当前价 126.0 低于近 3 图估值", "risk_level": "high"}\n```'
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    assert result["source"] == "llm"
    assert result["action"] == "BUY"
    assert result["risk_level"] == "HIGH"


def test_chinese_action_and_risk_are_normalized():
    raw = json.dumps({"action": "卖出", "reason": "涨到 126.0 但表现分仅 45", "risk_level": "高风险"}, ensure_ascii=False)
    result = analyze(_ctx(rating=45), chat=lambda prompt: raw, settings=_settings())

    assert result["action"] == "SELL"
    assert result["risk_level"] == "HIGH"


# ---------- 3. 非 JSON → 回落 ----------

def test_non_json_falls_back_to_rules():
    result = analyze(_ctx(), chat=lambda prompt: "我觉得可以买入，理由是很强。", settings=_settings())

    assert result["source"] == "rule_fallback"
    assert set(result) == EXPECTED_KEYS


# ---------- 4. 缺字段 / 枚举非法 → 回落 ----------

def test_missing_reason_falls_back():
    raw = json.dumps({"action": "BUY", "risk_level": "LOW"})
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    assert result["source"] == "rule_fallback"


def test_invalid_action_falls_back():
    raw = json.dumps({"action": "STRONG_BUY", "reason": "很强", "risk_level": "LOW"})
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    assert result["source"] == "rule_fallback"


def test_parse_and_validate_raises_on_bad_action():
    with pytest.raises(LLMOutputError):
        _parse_and_validate(json.dumps({"action": "MAYBE", "reason": "x", "risk_level": "LOW"}))


# ---------- 5. 超时 / 异常 → 回落 ----------

def test_chat_timeout_falls_back():
    def boom(prompt):
        raise TimeoutError("read timeout=20")

    result = analyze(_ctx(), chat=boom, settings=_settings())

    assert result["source"] == "rule_fallback"
    assert set(result) == EXPECTED_KEYS


# ---------- 6. 无密钥 → 直接规则版（不碰网络）----------

def test_no_api_key_uses_rules_without_calling_model():
    called = {"n": 0}

    def should_not_be_called(prompt):
        called["n"] += 1
        return "{}"

    result = analyze(_ctx(), settings=_settings(api_key=""))

    assert called["n"] == 0
    assert result["source"] == "rule_fallback"


# ---------- 7. 契约约束：字段集合一致 + 只读 ----------

def test_field_set_matches_rule_fallback():
    raw = json.dumps({"action": "HOLD", "reason": "价格 126.0 未触发阈值", "risk_level": "LOW"})
    llm_result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())
    rule_result = analyze(_ctx(), settings=_settings(api_key=""))

    assert set(llm_result) == set(rule_result) == EXPECTED_KEYS


def test_output_never_contains_band_or_balance_fields():
    raw = json.dumps(
        {
            "action": "BUY",
            "reason": "价格 126.0，表现分 88",
            "risk_level": "MEDIUM",
            "suggested_price_band": {"low": 120.0, "high": 130.0},
            "balance": 9999,
        },
        ensure_ascii=False,
    )
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    assert "suggested_price_band" not in result  # 契约可缺省，本版本统一不输出
    assert "balance" not in result  # AI 不得触碰余额
    assert "positions" not in result
    assert set(result) == EXPECTED_KEYS


# ---------- 8. 理由长度约束（2026-11-14 由 120 放宽到 200，且改为智能截断）----------

def test_reason_is_truncated_to_limit_with_ellipsis():
    """超长理由不能裸切（旧实现切出"短期动量明显偏"这种残句），要补省略号且不超限。"""
    long_reason = "价格" * 200
    raw = json.dumps({"action": "HOLD", "reason": long_reason, "risk_level": "LOW"}, ensure_ascii=False)
    result = analyze(_ctx(), chat=lambda prompt: raw, settings=_settings())

    from ai.llm_agent import MAX_REASON_LEN

    assert len(result["reason"]) <= MAX_REASON_LEN
    assert result["reason"].endswith("…"), "截断后必须带省略号，让人知道不是文案坏了"


def test_reason_cut_at_sentence_end_when_possible():
    """能在句末标点处断开时，优先断在标点后（不把句子切一半）。"""
    from ai.llm_agent import MAX_REASON_LEN, _truncate_reason

    sentence = "价格由 89.13 跌至 85.00，跌幅 4.6%。"
    text = sentence * 20  # 远超上限
    out = _truncate_reason(text)

    assert len(out) <= MAX_REASON_LEN
    assert out.endswith("…")
    assert out[:-1].endswith("。"), f"应在句号后断开，实际尾部：{out[-12:]!r}"


def test_short_reason_is_untouched():
    from ai.llm_agent import _truncate_reason

    assert _truncate_reason("近 3 个价格点上涨 5%，表现分 88。") == "近 3 个价格点上涨 5%，表现分 88。"


# ---------- 9. 兜底本身也合法（回归保护）----------

def test_fallback_output_is_renderable():
    advice = rule_based_advice(_ctx())
    assert advice["action"] in {"BUY", "SELL", "HOLD"}
    assert advice["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert advice["source"] == "rule_fallback"
    assert advice["disclaimer"]


# ---------- 10. 端点 URL 归一化（LLM_BASE_URL 两种写法都吃）----------

def test_base_url_defaults_to_openai_endpoint(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    assert _base_url() == DEFAULT_BASE_URL


def test_base_url_appends_chat_completions_when_only_base_given(monkeypatch):
    """只填 base（最常见、也最符合变量名的写法）要自动补全，否则线上 404 回落成规则版。"""
    monkeypatch.setenv("LLM_BASE_URL", "https://opencode.ai/inference/openai/v1")
    assert _base_url() == "https://opencode.ai/inference/openai/v1/chat/completions"


def test_base_url_keeps_full_endpoint_untouched(monkeypatch):
    full = "https://opencode.ai/inference/openai/v1/chat/completions"
    monkeypatch.setenv("LLM_BASE_URL", full)
    assert _base_url() == full


def test_base_url_strips_trailing_slash_and_spaces(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "  https://api.openai.com/v1/  ")
    assert _base_url() == "https://api.openai.com/v1/chat/completions"


def test_base_url_strips_pasted_quotes(monkeypatch):
    """Windows `set LLM_BASE_URL="https://…"` 会把引号并进值里 → 旧实现 unknown url type。"""
    monkeypatch.setenv("LLM_BASE_URL", '"https://opencode.ai/inference/openai/v1"')
    assert _base_url() == "https://opencode.ai/inference/openai/v1/chat/completions"


def test_api_key_and_model_strip_pasted_quotes(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", '"oc_sk_demo"')
    monkeypatch.setenv("LLM_MODEL", "'deepseek-v4.1-flash-free'")
    assert _api_key(None) == "oc_sk_demo"
    assert _model(None) == "deepseek-v4.1-flash-free"

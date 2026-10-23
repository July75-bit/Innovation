"""规则版降级建议单元测试。

负责人：D

只依赖标准库 + pytest，不需要任何模型密钥，可在 CI 里跑。
对应契约：`docs/software/api_contract.md` §4.10；规则表：`docs/algorithm/ai_agent_prompt.md` §5。
"""

from ai.fallback import rule_based_advice

VALID_ACTIONS = {"BUY", "SELL", "HOLD"}
VALID_RISKS = {"LOW", "MEDIUM", "HIGH"}
REQUIRED_KEYS = {"player_id", "action", "reason", "risk_level", "source", "disclaimer"}


def _ctx(**overrides):
    """一份正常行情上下文（默认：横盘、持仓 2 股）。"""
    ctx = {
        "player_id": 1,
        "name": "ZywOo",
        "current_price": 126.0,
        "change_pct": 0.0,
        "rating": 88,
        "recent_prices": [{"ts": "t1", "price": 126.0}, {"ts": "t2", "price": 126.0}],
        "position": {"quantity": 2, "avg_cost": 120.0},
    }
    ctx.update(overrides)
    return ctx


def test_rise_with_low_rating_sells():
    """涨得多但表现分低 -> SELL / HIGH"""
    ctx = _ctx(
        rating=45,
        recent_prices=[{"price": 100.0}, {"price": 108.0}],  # +8%
    )
    out = rule_based_advice(ctx)

    assert out["action"] == "SELL"
    assert out["risk_level"] == "HIGH"
    assert "8.0%" in out["reason"]


def test_fall_with_high_rating_buys():
    """跌得多但表现分高 -> BUY / MEDIUM"""
    ctx = _ctx(
        rating=82,
        recent_prices=[{"price": 120.0}, {"price": 110.0}],  # -8.33%
    )
    out = rule_based_advice(ctx)

    assert out["action"] == "BUY"
    assert out["risk_level"] == "MEDIUM"


def test_normal_range_holds():
    """波动未触发阈值 -> HOLD / LOW"""
    ctx = _ctx(rating=70, recent_prices=[{"price": 100.0}, {"price": 102.0}])
    out = rule_based_advice(ctx)

    assert out["action"] == "HOLD"
    assert out["risk_level"] == "LOW"


def test_sell_downgraded_when_no_position():
    """命中 SELL 但无持仓 -> 降级 HOLD（避免建议做不到的动作）"""
    ctx = _ctx(
        rating=45,
        recent_prices=[{"price": 100.0}, {"price": 110.0}],
        position={"quantity": 0, "avg_cost": 0},
    )
    out = rule_based_advice(ctx)

    assert out["action"] == "HOLD"
    assert out["risk_level"] == "LOW"
    assert "无持仓" in out["reason"]


def test_output_shape_and_enums():
    """结构、枚举、来源标记、免责声明必须符合契约"""
    out = rule_based_advice(_ctx())

    assert REQUIRED_KEYS.issubset(out.keys())
    assert out["action"] in VALID_ACTIONS
    assert out["risk_level"] in VALID_RISKS
    assert out["source"] == "rule_fallback"
    assert out["disclaimer"]
    assert len(out["reason"]) <= 120
    assert "suggested_price_band" not in out  # 契约里可缺省，规则版不编造区间


def test_missing_fields_do_not_raise():
    """字段缺失 / 非法值也不能抛异常，且仍返回合法结构"""
    for bad_ctx in ({}, {"player_id": 9}, {"rating": None, "recent_prices": None},
                    {"rating": "abc", "change_pct": "x", "recent_prices": "oops"}):
        out = rule_based_advice(bad_ctx)
        assert out["action"] in VALID_ACTIONS
        assert out["risk_level"] in VALID_RISKS
        assert out["source"] == "rule_fallback"

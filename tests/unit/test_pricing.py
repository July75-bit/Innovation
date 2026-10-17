"""定价算法单元测试。

负责人：C（实现后把 skip 去掉）

保留 skip 的原因：backend/pricing/pricing.py 目前是契约骨架（raise NotImplementedError），
先写上预期行为，C 第 2 天实现时先改测试跑通再改实现（课程要求 TDD）。
"""

import pytest

from pricing.pricing import update_price


@pytest.mark.skip(reason="C 同学第 2 天实现 update_price 后取消 skip")
def test_price_rises_when_score_positive() -> None:
    result = update_price(100.0, score_delta=0.5, alpha=0.2)

    assert result.new_price == pytest.approx(110.0)
    assert result.change_pct == pytest.approx(10.0)
    assert result.reason  # 必须有人类可读的变化原因


@pytest.mark.skip(reason="C 同学实现后取消 skip")
def test_price_falls_when_score_negative() -> None:
    result = update_price(100.0, score_delta=-0.5, alpha=0.2)

    assert result.new_price == pytest.approx(90.0)
    assert result.change_pct < 0
    assert result.reason


@pytest.mark.skip(reason="C 同学实现后取消 skip")
def test_price_never_below_floor() -> None:
    result = update_price(2.0, score_delta=-1.0, alpha=5.0, floor=1.0)

    assert result.new_price >= 1.0


@pytest.mark.skip(reason="C 同学实现后取消 skip")
def test_zero_demand_signal_keeps_price_when_score_zero() -> None:
    result = update_price(100.0, score_delta=0.0, demand_signal=0.0)

    assert result.new_price == pytest.approx(100.0)
    assert result.change_pct == pytest.approx(0.0)


@pytest.mark.skip(reason="C 同学实现后取消 skip")
def test_invalid_current_price_raises() -> None:
    with pytest.raises(ValueError):
        update_price(0.0, score_delta=0.1)

"""定价算法单元测试。

负责人：C

第 1 天已实现 `update_price` / `standardize_score`，本文件中的 skip 全部移除。

运行方式：
- pytest（仓库根目录）：`python -m pytest tests/unit/test_pricing.py -v`
- 零依赖直跑（没装 pytest 也能用）：`python tests/unit/test_pricing.py`

实现说明：断言只用标准库 `assert` + 容差函数，不依赖 pytest 的 `approx/raises`，
这样 pytest 能发现并运行这些用例，没装 pytest 的机器也能独立跑。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from core_engine.pricing import MAX_STEP_PCT, standardize_score, update_price  # noqa: E402

TOL = 1e-6


def _close(actual: float, expected: float, tol: float = TOL) -> bool:
    return abs(float(actual) - float(expected)) <= tol


def test_price_rises_when_score_positive() -> None:
    result = update_price(100.0, score_delta=0.5, alpha=0.2)

    assert _close(result.new_price, 110.0), result.new_price
    assert _close(result.change_pct, 10.0), result.change_pct
    assert result.reason  # 必须有人类可读的变化原因
    assert "上涨" in result.reason


def test_price_falls_when_score_negative() -> None:
    result = update_price(100.0, score_delta=-0.5, alpha=0.2)

    assert _close(result.new_price, 90.0), result.new_price
    assert result.change_pct < 0
    assert result.reason
    assert "下跌" in result.reason


def test_price_never_below_floor() -> None:
    """无论参数多极端，价格都不会低于 floor（原 Day1 用例，保留最弱断言）。"""

    result = update_price(2.0, score_delta=-1.0, alpha=5.0, floor=1.0)

    assert result.new_price >= 1.0
    assert result.new_price > 0
    # 对称 clamp 下这一档先被截到 1.60（未触底），触底细节见 test_floor_applies_after_clamp
    assert _close(result.new_price, 1.6), result.new_price


def test_zero_demand_signal_keeps_price_when_score_zero() -> None:
    result = update_price(100.0, score_delta=0.0, demand_signal=0.0)

    assert _close(result.new_price, 100.0), result.new_price
    assert _close(result.change_pct, 0.0), result.change_pct
    assert "维持不变" in result.reason


def test_invalid_current_price_raises() -> None:
    try:
        update_price(0.0, score_delta=0.1)
    except ValueError:
        return
    raise AssertionError("current_price <= 0 时必须抛 ValueError")


def test_step_is_capped_symmetrically() -> None:
    """单次变动封顶 ±20%（对称）：涨跌都按上限执行。"""

    up = update_price(100.0, score_delta=1.0, alpha=5.0)   # 原始 +500%
    assert up.capped is True
    assert _close(up.new_price, 100.0 * (1 + MAX_STEP_PCT)), up.new_price
    assert "上限" in up.reason

    down = update_price(100.0, score_delta=-1.0, alpha=5.0)  # 原始 -500%
    assert down.capped is True
    assert _close(down.new_price, 100.0 * (1 - MAX_STEP_PCT)), down.new_price
    assert _close(down.change_pct, -MAX_STEP_PCT * 100), down.change_pct


def test_floor_applies_after_clamp() -> None:
    """clamp 之后若仍低于 floor（价格已经很低），价格停在 floor。"""

    # P=1.1、S=-1、α=0.15 → -15% → 0.935 < floor=1.0 → 停在 1.00
    result = update_price(1.1, score_delta=-1.0, alpha=0.15, floor=1.0)
    assert result.capped is False
    assert result.floored is True
    assert _close(result.new_price, 1.0), result.new_price
    assert "下限" in result.reason


def test_standardize_score_basics() -> None:
    assert _close(standardize_score(80.0, []), 0.0)              # 空历史
    assert _close(standardize_score(80.0, [80.0, 80.0]), 0.0)    # 零标准差

    high = standardize_score(95.0, [70.0, 72.0, 74.0])
    low = standardize_score(50.0, [70.0, 72.0, 74.0])
    assert high > 0 > low
    assert -1.0 <= low <= high <= 1.0


def test_reason_includes_score_when_provided() -> None:
    """第 4 天验收：reason 要能追溯到"本轮得分"；不传 score 时保持旧文案（B 会补）。"""
    with_score = update_price(100.0, score_delta=0.5, alpha=0.2, score=88.0)
    assert "本轮得分 88.0" in with_score.reason, with_score.reason
    assert "S=+0.50" in with_score.reason, with_score.reason

    without_score = update_price(100.0, score_delta=0.5, alpha=0.2)
    assert "得分" not in without_score.reason, without_score.reason


def test_standardize_score_three_sigma_scale() -> None:
    """1σ → S≈0.333、2σ → 0.667、3σ → 满格 1.0：证明实现的是 z/Z_FULL_SCALE 而非 clamp(z)。"""

    history = [70.0, 72.0, 74.0]        # 均值 72，总体标准差 ≈ 1.6330
    sd = 1.632993161855452

    assert _close(standardize_score(72 + sd, history), 1 / 3, 1e-3)
    assert _close(standardize_score(72 + 2 * sd, history), 2 / 3, 1e-3)
    assert _close(standardize_score(72 + 3 * sd, history), 1.0, 1e-3)
    assert _close(standardize_score(72 + 10 * sd, history), 1.0)  # 超过 3σ 仍饱和


def test_z_full_scale_one_matches_literal_mapping() -> None:
    """Z_FULL_SCALE 改成 1.0 时回到字面口径 clamp(z,-1,1)：1σ 即满格。"""

    import core_engine.pricing as pricing_mod

    history = [70.0, 72.0, 74.0]
    sd = 1.632993161855452
    original = pricing_mod.Z_FULL_SCALE
    try:
        pricing_mod.Z_FULL_SCALE = 1.0
        assert _close(standardize_score(72 + sd, history), 1.0)
        assert _close(standardize_score(72 + 0.5 * sd, history), 0.5)
    finally:
        pricing_mod.Z_FULL_SCALE = original


# ---------------------------------------------------------------- 零依赖运行器
def _run_all() -> int:
    """没有 pytest 也能跑（课程环境/CI 未装依赖时用）。"""
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failed = 0
    print(f"运行 {len(tests)} 个定价测试 …\n")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n结果：{len(tests) - failed}/{len(tests)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())

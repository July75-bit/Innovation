"""定价引擎的入参校验与配置回落（2026-11-07 补强）。

为什么单独一个文件：这些分支平时不走——非法入参、配置读不到、环境变量覆盖。
但它们正是"参数错了要立刻报错，而不是算出一个坏价格"的保障，
所以按「守卫（guard）」而不是「正常路径」归类。

不修改 `core_engine/pricing.py` 一行代码。
"""

from __future__ import annotations

import sys

import pytest

from core_engine import pricing


# ---------------------------------------------------------------- 配置解析

def test_env_float_reads_valid_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PS_TEST_FLOAT", "0.25")
    assert pricing._env_float("PS_TEST_FLOAT") == pytest.approx(0.25)


def test_env_float_missing_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PS_TEST_FLOAT", raising=False)
    assert pricing._env_float("PS_TEST_FLOAT") is None


def test_env_float_blank_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PS_TEST_FLOAT", "   ")
    assert pricing._env_float("PS_TEST_FLOAT") is None


def test_env_float_invalid_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """写成 'abc' 不应抛异常，只是当作没配置。"""
    monkeypatch.setenv("PS_TEST_FLOAT", "abc")
    assert pricing._env_float("PS_TEST_FLOAT") is None


def test_settings_returns_none_when_backend_config_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """脚本/单测场景下 app 包可能不在，定价必须仍可用。

    注意：`_settings()` 带 `lru_cache`，前面的用例可能已把真实配置缓存进来，
    所以必须先 `cache_clear()` 才能走到"import 失败 → return None"这条分支。
    """
    monkeypatch.setitem(sys.modules, "app.core.config", None)
    pricing._settings.cache_clear()
    try:
        assert pricing._settings() is None
    finally:
        pricing._settings.cache_clear()  # 别把 None 缓存留给后面的用例


def test_resolve_prefers_env_over_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pricing, "_settings", lambda: None)
    monkeypatch.setenv(pricing._ENV_ALPHA, "0.08")
    resolved = pricing._resolve(
        None, "pricing_alpha", pricing._ENV_ALPHA, pricing.DEFAULT_ALPHA
    )
    assert resolved == pytest.approx(0.08)


def test_resolve_falls_back_to_module_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pricing, "_settings", lambda: None)
    monkeypatch.delenv(pricing._ENV_ALPHA, raising=False)
    resolved = pricing._resolve(
        None, "pricing_alpha", pricing._ENV_ALPHA, pricing.DEFAULT_ALPHA
    )
    assert resolved == pytest.approx(pricing.DEFAULT_ALPHA)


# ---------------------------------------------------------------- 需求项文案

def test_reason_mentions_demand_when_beta_enabled() -> None:
    """β>0 且需求信号显著时，reason 要说明"买盘/卖盘集中"，便于归因。"""
    update = pricing.update_price(
        100.0, 0.0, demand_signal=0.5, beta=0.05, alpha=0.0
    )
    assert "买盘集中" in update.reason
    assert "净买入占比 50%" in update.reason


def test_reason_mentions_sell_side_when_demand_negative() -> None:
    update = pricing.update_price(
        100.0, 0.0, demand_signal=-0.5, beta=0.05, alpha=0.0
    )
    assert "卖盘集中" in update.reason


# ---------------------------------------------------------------- 入参校验

def test_update_price_rejects_non_finite_score_delta() -> None:
    with pytest.raises(ValueError, match="score_delta"):
        pricing.update_price(100.0, None)  # type: ignore[arg-type]


def test_update_price_rejects_non_finite_demand_signal() -> None:
    with pytest.raises(ValueError, match="demand_signal"):
        pricing.update_price(100.0, 0.1, demand_signal=None)  # type: ignore[arg-type]


def test_update_price_rejects_non_finite_score() -> None:
    with pytest.raises(ValueError, match="score"):
        pricing.update_price(100.0, 0.1, score=float("inf"))


def test_update_price_rejects_negative_alpha() -> None:
    with pytest.raises(ValueError, match="不能为负"):
        pricing.update_price(100.0, 0.1, alpha=-0.1)


def test_update_price_rejects_non_positive_floor() -> None:
    with pytest.raises(ValueError, match="floor"):
        pricing.update_price(100.0, 0.1, floor=0)


def test_standardize_score_rejects_window_below_one() -> None:
    with pytest.raises(ValueError, match="window"):
        pricing.standardize_score(80.0, [70.0, 75.0], window=0)


def test_standardize_score_rejects_non_finite_raw_score() -> None:
    with pytest.raises(ValueError, match="raw_score"):
        pricing.standardize_score(None, [70.0, 75.0])  # type: ignore[arg-type]

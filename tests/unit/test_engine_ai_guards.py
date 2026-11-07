"""引擎与 AI 侧的边界兜底：空输入、非法选手、上下文组装失败。

为什么单独一个文件：这些都是"数据不完整"时系统还能不能体面活着的问题——
空选手列表要不要崩、需求信号除零怎么办、AI 上下文彻底拼不出来时能否仍返回 200。

不修改 `core_engine/simulator.py` / `app/core/price_update.py` / `app/api/ai.py`。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.models import Player
from app.core import price_update
from core_engine import simulator


# ---------------------------------------------------------------- 随机源与序列生成

def test_rng_without_seed_is_still_usable() -> None:
    """不传 seed 时退化为普通随机源，而不是报错。"""
    rng = simulator._rng(None, player_id=1, round_no=1)
    assert 0.0 <= rng.random() < 1.0


def test_generate_series_rejects_non_positive_rounds() -> None:
    with pytest.raises(ValueError, match="rounds"):
        simulator.generate_match_series([1, 2], 0)


def test_generate_series_returns_empty_for_no_players() -> None:
    """没有选手就是空序列，不该抛异常（脚本空库场景）。"""
    assert simulator.generate_match_series([], 3) == []


# ---------------------------------------------------------------- 需求信号

def test_demand_signal_zero_volume_avoids_division() -> None:
    assert simulator.to_demand_signal(10.0, 0.0) == 0.0


def test_demand_signal_missing_volume_returns_zero() -> None:
    assert simulator.to_demand_signal(10.0, None) == 0.0  # type: ignore[arg-type]
    assert simulator.to_demand_signal(10.0, float("nan")) == 0.0


def test_demand_signal_missing_net_buy_returns_zero() -> None:
    assert simulator.to_demand_signal(None, 100.0) == 0.0  # type: ignore[arg-type]


def test_demand_signal_is_clamped_to_unit_range() -> None:
    assert simulator.to_demand_signal(150.0, 100.0) == 1.0
    assert simulator.to_demand_signal(-150.0, 100.0) == -1.0
    assert simulator.to_demand_signal(25.0, 100.0) == pytest.approx(0.25)


# ---------------------------------------------------------------- 待落库变更

def _player(**kwargs) -> Player:
    base = {
        "player_id": 1,
        "name": "ZywOo",
        "display_name": "ZywOo",
        "team": "Vitality",
        "role": "AWPer",
        "current_price": Decimal("126.00"),
        "prev_price": Decimal("120.00"),
        "rating": 88,
        "status": "trading",
    }
    base.update(kwargs)
    return Player(**base)


def test_planned_update_display_has_sign_and_reason() -> None:
    planned = price_update.PlannedUpdate(
        player_id=1,
        name="ZywOo",
        old_price=Decimal("120.00"),
        new_price=Decimal("126.00"),
        change_pct=5.0,
        reason="测试",
    )
    text = planned.display
    assert "+5.00%" in text
    assert "120.00 → 126.00" in text


def test_plan_for_player_rejects_missing_player() -> None:
    with pytest.raises(ValueError, match="player"):
        price_update.plan_for_player(None, lambda price: None)  # type: ignore[arg-type,return-value]


def test_plan_for_player_rejects_non_positive_price() -> None:
    with pytest.raises(ValueError, match="非法"):
        price_update.plan_for_player(_player(current_price=Decimal("0")), lambda price: None)  # type: ignore[arg-type,return-value]


def test_plan_updates_returns_empty_for_no_players() -> None:
    """空批次直接返回空列表，不调用计算器。"""
    assert price_update.plan_updates([], lambda price: None) == []  # type: ignore[arg-type,return-value]


def test_apply_updates_returns_empty_for_empty_plan(session_factory) -> None:
    """没有待落库变更时不开事务、不写库。"""
    with session_factory() as db:
        assert price_update.apply_updates(db, []) == []


# ---------------------------------------------------------------- AI 最小上下文

def test_minimal_context_keeps_required_fields() -> None:
    """上下文拼不出来时的兜底：字段够规则版算出一条建议即可。"""
    from app.api.ai import _minimal_context

    context = _minimal_context(_player())

    assert context["context_source"] == "minimal"
    assert context["player_id"] == 1
    assert context["current_price"] == pytest.approx(126.0)
    assert context["change_pct"] == pytest.approx(5.0)
    assert context["position"] == {"quantity": 0.0, "avg_cost": 0.0}


def test_analysis_endpoint_survives_context_failure(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """上下文组装整个炸掉时，仍然 200 + 规则版建议，绝不 5xx。"""
    def _boom(*_args, **_kwargs):
        raise RuntimeError("seed 文件都读不到")

    monkeypatch.setattr("app.api.ai.build_player_context", _boom)

    response = client.get("/api/analysis/1")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "rule_fallback"
    assert body["player_id"] == 1

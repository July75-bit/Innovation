"""交易规则纯函数测试（不依赖数据库，毫秒级）。

负责人：B

覆盖 core/rules.py 的边界：金额取整、余额边界、持仓上限边界、持仓不足、暂停交易。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import ApiError
from app.core.rules import (
    calc_amount,
    ensure_available_position,
    ensure_position_limit,
    ensure_sufficient_balance,
    ensure_tradable,
)


def test_calc_amount_rounds_to_cent():
    assert calc_amount(Decimal("126.00"), 2) == Decimal("252.00")
    assert calc_amount(Decimal("126.005"), 1) == Decimal("126.01")
    assert calc_amount(Decimal("0.10"), 3) == Decimal("0.30")


def test_sufficient_balance_boundary():
    # 余额刚好等于成交金额：允许
    ensure_sufficient_balance(Decimal("252.00"), Decimal("252.00"))

    with pytest.raises(ApiError) as excinfo:
        ensure_sufficient_balance(Decimal("251.99"), Decimal("252.00"))
    assert excinfo.value.status_code == 400
    assert excinfo.value.code == "INSUFFICIENT_BALANCE"
    assert "余额不足" in excinfo.value.message


def test_position_limit_boundary():
    # 45 + 5 = 50，刚好到上限：允许
    ensure_position_limit(45, 5, limit=50)

    with pytest.raises(ApiError) as excinfo:
        ensure_position_limit(46, 5, limit=50)
    assert excinfo.value.code == "POSITION_LIMIT_EXCEEDED"
    assert "持仓上限" in excinfo.value.message


def test_available_position_boundary():
    ensure_available_position(2, 2)

    with pytest.raises(ApiError) as excinfo:
        ensure_available_position(2, 3)
    assert excinfo.value.code == "INSUFFICIENT_POSITION"
    assert "持仓不足" in excinfo.value.message


def test_only_trading_player_is_tradable():
    ensure_tradable("trading")

    with pytest.raises(ApiError) as excinfo:
        ensure_tradable("suspended")
    assert excinfo.value.code == "PLAYER_TRADING_SUSPENDED"
    assert "暂停交易" in excinfo.value.message

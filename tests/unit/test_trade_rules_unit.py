"""交易规则纯函数测试（不依赖数据库，毫秒级）。

负责人：B

覆盖 core/rules.py 的边界：金额取整、余额边界、持仓上限边界、持仓不足、暂停交易，
以及第 5 天补的"错误信息要给出下一步"（Nielsen「错误可恢复：原因 + 下一步」）。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import ApiError
from app.core.demo_schedule import DEMO_SCHEDULE
from app.core.rules import (
    calc_amount,
    ensure_available_position,
    ensure_position_limit,
    ensure_sufficient_balance,
    ensure_tradable,
    ensure_tradable_now,
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


# ---------- 第 5 天：错误信息必须给"下一步" ----------


def test_insufficient_balance_tells_max_affordable_quantity():
    """余额不足时要说"按当前价最多还能买几股"，而不是只甩两个数字。"""
    with pytest.raises(ApiError) as excinfo:
        ensure_sufficient_balance(Decimal("300.00"), Decimal("1260.00"), price=Decimal("126.00"))

    message = excinfo.value.message
    assert "余额不足" in message
    assert "最多可买 2 股" in message  # 300 // 126 = 2


def test_insufficient_balance_when_cannot_afford_one_share():
    with pytest.raises(ApiError) as excinfo:
        ensure_sufficient_balance(Decimal("50.00"), Decimal("126.00"), price=Decimal("126.00"))

    assert "买不起 1 股" in excinfo.value.message


def test_insufficient_balance_without_price_keeps_old_wording():
    """不传 price 时退化成原来的提示（兼容旧调用）。"""
    with pytest.raises(ApiError) as excinfo:
        ensure_sufficient_balance(Decimal("251.99"), Decimal("252.00"))

    assert "需要 252.00" in excinfo.value.message
    assert "最多可买" not in excinfo.value.message


def test_position_limit_tells_remaining_quantity():
    with pytest.raises(ApiError) as excinfo:
        ensure_position_limit(46, 5, limit=50)

    assert "最多还能买 4 股" in excinfo.value.message


def test_position_limit_when_already_full():
    with pytest.raises(ApiError) as excinfo:
        ensure_position_limit(50, 1, limit=50)

    assert "已持满 50 股" in excinfo.value.message


def test_available_position_tells_max_sellable_and_guides_empty_holder():
    with pytest.raises(ApiError) as excinfo:
        ensure_available_position(2, 5)
    assert "最多可卖 2 股" in excinfo.value.message

    with pytest.raises(ApiError) as excinfo:
        ensure_available_position(0, 1)
    assert "请先买入" in excinfo.value.message


# ---------------- 第 8 轮：本轮赛程派生的停牌也要挡住下单 ----------------
# 背景：players.status 存的是"初始 / 运维手动"状态，"本轮在打比赛"是按赛程派生的。
# 只查前者就会出现"界面显示暂停交易、接口照样收单"，所以闸门必须两层都看。


def test_tradable_now_blocks_playing_team() -> None:
    """第 12 轮 Vitality vs Spirit：两队整队拦单，其余队伍照常。"""
    with pytest.raises(ApiError) as excinfo:
        ensure_tradable_now("trading", "Vitality", round_no=12, schedule=DEMO_SCHEDULE)
    assert excinfo.value.status_code == 400
    assert excinfo.value.code == "PLAYER_TRADING_SUSPENDED"
    assert "Vitality vs Spirit 比赛中，暂停交易" in excinfo.value.message

    ensure_tradable_now("trading", "FaZe Clan", round_no=12, schedule=DEMO_SCHEDULE)


def test_tradable_now_manual_status_wins_and_keeps_contract_message() -> None:
    """手动冻结优先：文案沿用契约 §4.7 原句，不掺赛程信息。"""
    with pytest.raises(ApiError) as excinfo:
        ensure_tradable_now("suspended", "FaZe Clan", round_no=12, schedule=DEMO_SCHEDULE)
    assert excinfo.value.message == "该选手比赛进行中，暂停交易，请等结算完成后重试"


def test_tradable_now_outside_season_does_not_block_by_schedule() -> None:
    """round_no=None 且今天不是比赛日：只有手动 status 能拦单。"""
    ensure_tradable_now("trading", "Vitality", round_no=None, schedule={"matches": []})

    with pytest.raises(ApiError):
        ensure_tradable_now("halted", "Vitality", round_no=None, schedule={"matches": []})


def test_tradable_now_tolerates_unknown_team() -> None:
    """名单里有赛程外的队伍时不能把所有人拦在门外（自定义名单/旧数据）。"""
    ensure_tradable_now("trading", "不存在的队", round_no=12, schedule=DEMO_SCHEDULE)

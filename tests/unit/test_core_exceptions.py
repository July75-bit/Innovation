"""核心异常路径验收（T4-06 / 课程第 4 天 p.177–178）。

负责人：D

覆盖「正常路径之外」最容易在演示现场被老师点到的分支：
- 卖出暂停交易选手 → 400 `PLAYER_TRADING_SUSPENDED`
- 卖出不存在的选手 → 404 `PLAYER_NOT_FOUND`
- 买入缺字段 → 422（Pydantic 校验，不落到业务层）
- 查询不存在选手的价格历史 → 404 JSON（不是 500 / 空数组）
- 卖出超过持仓 → 400 `INSUFFICIENT_POSITION`，且账户完全不变（不产生半笔交易）

这些用例与 `test_trades_rule.py` / `test_api_trades.py` 的既有断言互补：
那边按「一个接口一组参数」写，这里按「答辩会被追问的异常矩阵」集中守一遍。
"""

from __future__ import annotations

import pytest

SUSPENDED_PLAYER = 7  # 种子数据里 sh1ro 是 suspended
UNKNOWN_PLAYER = 999


def _sell(client, **body):
    return client.post("/api/trades/sell", json=body)


def test_sell_suspended_player_returns_400(client) -> None:
    """暂停交易选手不能卖出（与买入同一条状态检查）。"""
    response = _sell(client, player_id=SUSPENDED_PLAYER, quantity=1)

    assert response.status_code == 400
    assert response.json()["code"] == "PLAYER_TRADING_SUSPENDED"


def test_sell_unknown_player_returns_404(client) -> None:
    response = _sell(client, player_id=UNKNOWN_PLAYER, quantity=1)

    assert response.status_code == 404
    assert response.json()["code"] == "PLAYER_NOT_FOUND"


@pytest.mark.parametrize("body", [{}, {"player_id": 1}, {"quantity": 1}])
def test_buy_missing_fields_returns_422(client, body) -> None:
    """缺 player_id / quantity 由请求模型拦下，返回 422 而不是 500。"""
    response = client.post("/api/trades/buy", json=body)

    assert response.status_code == 422


def test_prices_unknown_player_returns_404_json(client) -> None:
    response = client.get(f"/api/players/{UNKNOWN_PLAYER}/prices")

    assert response.status_code == 404
    assert response.json()["code"] == "PLAYER_NOT_FOUND"


def test_sell_more_than_held_keeps_account_unchanged(client) -> None:
    """卖超持仓：返回 400，余额/总资产/持仓都不变（失败即回滚）。"""
    before_account = client.get("/api/account").json()
    before_positions = client.get("/api/positions").json()

    response = _sell(client, player_id=1, quantity=999)

    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_POSITION"
    assert client.get("/api/account").json() == before_account
    assert client.get("/api/positions").json() == before_positions

"""端到端集成测试：一条主链路打通前后端依赖的全部接口。

负责人：D（牵头） + B（接口）

主链路（第 3 天必须跑通，第 5 天线上再验一次）：

    GET  /api/players           拿市场列表
    GET  /api/account           拿初始余额 5000
    POST /api/trades/buy        买入 2 股
    GET  /api/positions         持仓出现该选手
    GET  /api/trades            流水里有一条 BUY
    GET  /api/players/{id}/prices  价格历史非空
    POST /api/trades/sell       卖出 1 股
    GET  /api/account           余额比买入后增加
    GET  /api/analysis/{id}     返回合法结构的建议（AI 或 rule_fallback 均可）
"""

import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="B/A 完成接口后由 D 取消 skip，第 3 天起作为回归用例")
def test_full_trade_flow(client) -> None:
    """完整交易闭环。"""


@pytest.mark.integration
@pytest.mark.skip(reason="第 4 天后启用")
def test_ai_analysis_always_returns_valid_shape(client) -> None:
    """无论模型是否可用，AI 接口都必须返回可渲染的结构（source 为 llm 或 rule_fallback）。"""

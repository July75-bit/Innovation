"""交易规则边界测试（B 的 D4 验收点）。

负责人：B

这些是用例清单，不是摆设：分工文档明确要求测试
"余额不足、持仓不足、非法数量、无效选手、持仓上限、暂停交易"，
全部通过才算交易系统 D4 交付。
"""

import pytest


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_buy_normal(client) -> None:
    """正常买入：余额减少、持仓增加、生成一条 BUY 流水。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_buy_insufficient_balance(client) -> None:
    """余额不足 -> 400，且余额、持仓、流水都不变。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_buy_invalid_quantity(client) -> None:
    """quantity 为 0 / 负数 / 小数 / 非数字 -> 422 或 400。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_buy_invalid_player(client) -> None:
    """选手不存在 -> 404。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_buy_exceeds_position_limit(client) -> None:
    """单选手持仓超过 50 股 -> 400。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_sell_more_than_held(client) -> None:
    """卖出数量大于持仓 -> 400，不允许卖空。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_sell_normal(client) -> None:
    """正常卖出：余额增加、持仓减少或归零、生成一条 SELL 流水。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_trade_uses_latest_price(client) -> None:
    """价格更新后成交必须用最新价，不能用户缓存价。"""


@pytest.mark.skip(reason="B 同学实现 /api/trades 后取消 skip")
def test_transaction_rollback_on_failure(client) -> None:
    """事务一致性：买入失败时余额、持仓、流水三者都不能被部分修改。"""

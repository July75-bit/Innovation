"""买入 / 卖出 / 交易流水。

负责人：B（实现） / A（前端调用） / C（成交价来源）

待实现：
- POST /api/trades/buy    买入
- POST /api/trades/sell   卖出
- GET  /api/trades        交易流水（按时间倒序）

请求统一结构：
    { "player_id": 1, "quantity": 2 }

成功响应统一结构（交易是否成功以后端数据库为准，前端不能只改数字）：
    { "success": true, "message": "买入成功", "balance": 4800, "player_id": 1, "quantity": 2 }

失败也要返回统一结构，HTTP 400：
    { "success": false, "message": "余额不足" }

必须校验的边界（B 的 D4 验收点）：
1. quantity 必须是正整数（不是 0、负数、小数、非数字）
2. 余额充足才能买入；成交价用"最新价格"，不是缓存价
3. 持仓足够才能卖出；不允许卖空
4. 单选手持仓上限 settings.max_position_per_player（50 股）
5. 选手不存在 -> 404；选手处于比赛暂停状态 -> 400
6. 余额 / 持仓 / 交易记录三者必须在同一个事务里提交，任何一步失败整体回滚
"""

from fastapi import APIRouter

router = APIRouter(prefix="/trades", tags=["trades"])

# TODO(B)：实现 POST /trades/buy、POST /trades/sell、GET /trades

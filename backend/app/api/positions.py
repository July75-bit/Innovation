"""持仓接口。

负责人：B（实现） / A（前端展示）

待实现：
- GET /api/positions   当前持仓列表

参考响应（列表项）：
    {
      "player_id": 1,
      "name": "Vex",
      "quantity": 10,
      "avg_cost": 120.0,
      "current_price": 126.0,
      "market_value": 1260.0,
      "profit": 60.0,
      "profit_pct": 5.0
    }

注意：
- 持仓为 0 的选手不要出现在列表里；
- avg_cost 是买入均价（含手续费时为含费成本，规则由 B 在 trade_plan 中确定并写进文档）。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/positions", tags=["positions"])

# TODO(B)：实现 GET /api/positions

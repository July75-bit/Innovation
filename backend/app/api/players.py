"""市场与选手接口。

负责人：B（实现） / A（前端消费） / C（价格字段来源）

契约见 docs/software/api_contract.md，字段名以契约为准，不要各写各的：
- 前端期待 player_id，后端就不能返回 id；
- C 输出 current_price，B 就不能存成 price。

待实现：
- GET /api/players                 市场列表（选手名、当前价、涨跌幅、表现评分）
- GET /api/players/{player_id}     单个选手详情（含最近一次价格变化原因）

参考响应（列表项）：
    {
      "player_id": 1,
      "name": "Shadow",
      "team": "Nova",
      "current_price": 103.5,
      "prev_price": 100.0,
      "change_pct": 3.5,
      "rating": 82,
      "status": "trading"
    }
"""

from fastapi import APIRouter

router = APIRouter(prefix="/players", tags=["players"])

# TODO(B)：按契约实现上面两个接口

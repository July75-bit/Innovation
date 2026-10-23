"""价格与行情历史接口（B 提供接口，数据由 C 的定价模块产生）。

负责人：B + C

待实现：
- GET /api/players/{player_id}/prices   价格历史（供 A 画折线图、D 做 AI 分析输入）

参考响应：
    {
      "player_id": 1,
      "points": [
        {"ts": "2026-01-01T10:00:00", "price": 120.0, "reason": "初始价格"},
        {"ts": "2026-01-01T10:05:00", "price": 126.0, "reason": "模拟比赛表现提升"}
      ]
    }

约定（第 1 天必须和 C 对齐，否则前端图表和 AI 输入都会崩）：
1. 时间必须升序，且能被 JavaScript `new Date()` 正确解析（建议 ISO 8601，带时区或统一 UTC）；
2. 每条点必须带 reason，这是"价格变化可解释"的落点，也是答辩演示要拆解的证据；
3. 空历史返回空数组 points: []，不要返回 404 —— 前端要区分"没有数据"和"选手不存在"。
"""

from fastapi import APIRouter

router = APIRouter(tags=["prices"])

# TODO(B)：实现 GET /players/{player_id}/prices（挂在 /api 前缀下）

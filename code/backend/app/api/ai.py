"""AI 分析接口（B 提供路由外壳，业务逻辑在 code/backend/ai/）。

负责人：D（业务） + B（路由/错误处理） + A（展示）

待实现：
- GET /api/analysis/{player_id}

输出契约（必须固定，前端按这个渲染）：
    {
      "player_id": 1,
      "action": "BUY",              # 只能是 BUY / SELL / HOLD
      "reason": "近 3 场表现评分持续上升，且价格尚未完全反映",
      "risk_level": "MEDIUM",       # LOW / MEDIUM / HIGH
      "suggested_price_band": {"low": 100.0, "high": 108.0},
      "source": "llm",              # llm / rule_fallback
      "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
    }

硬约束（三份材料都强调）：
1. API 密钥只在后端读取（settings.llm_api_key），绝不下发前端；
2. AI 只提供建议，**不直接修改余额或执行交易**；
3. 模型超时 / 返回非法 JSON / 无密钥时，必须回落到 code/backend/ai/fallback.py 的规则版，
   返回合法结构（source="rule_fallback"），并保证交易、定价、行情功能不受影响；
4. 单次调用要有超时（settings.llm_timeout_seconds），不能让前端挂死。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["ai"])

# TODO(D+B)：实现 GET /api/analysis/{player_id}

"""LLM 调用封装。

负责人：D

对外只暴露一个函数 `analyze(player_context) -> dict`，返回值结构固定，
由 app/api/ai.py 直接透传给前端，A 的页面按这个结构渲染。
"""

from typing import Any, Literal

Action = Literal["BUY", "SELL", "HOLD"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


def analyze(player_context: dict[str, Any]) -> dict[str, Any]:
    """分析单个选手并给出交易建议。

    Args:
        player_context: 由 B 组装的行情上下文，至少包含：
            {
              "player_id": 1,
              "name": "Shadow",
              "current_price": 103.5,
              "change_pct": 3.5,
              "rating": 82,
              "recent_prices": [{"ts": "...", "price": 100.0}, ...],
              "recent_reasons": ["模拟比赛表现提升", ...],
              "position": {"quantity": 10, "avg_cost": 98.0}
            }

    Returns:
        {
          "player_id": 1,
          "action": "BUY",                       # 只能是 BUY / SELL / HOLD
          "reason": "...",                        # 1-3 句中文，必须引用具体数据
          "risk_level": "MEDIUM",                 # LOW / MEDIUM / HIGH
          "suggested_price_band": {"low": 100.0, "high": 108.0},
          "source": "llm",                        # llm / rule_fallback
          "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
        }

    待实现（D）：
    1. 用 settings.llm_enabled 判断是否有密钥；无密钥直接走 fallback.rule_based_advice；
    2. 调模型时设置 settings.llm_timeout_seconds 超时；
    3. 模型输出必须做 JSON 校验：action 不在枚举内、缺字段、非 JSON 都视为失败 -> 回落；
    4. 任何异常都不能 500 抛给前端，最差也要返回 HOLD + rule_fallback。
    """
    raise NotImplementedError("D 同学实现 LLM 调用与 JSON 校验，失败时回落 fallback")


def _parse_and_validate(raw: str) -> dict[str, Any]:
    """解析模型返回的 JSON 文本并做结构校验（D 实现）。

    校验点：action ∈ {BUY, SELL, HOLD}；risk_level ∈ {LOW, MEDIUM, HIGH}；
    reason 非空；其他字段缺失时用默认值补齐。
    """
    raise NotImplementedError("D 同学实现")

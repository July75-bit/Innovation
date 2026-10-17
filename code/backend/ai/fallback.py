"""规则版降级建议（不依赖任何大模型）。

负责人：D

为什么要它：三份材料都把"AI 接口不稳定时系统仍能交易"列为硬要求。
第 5 天线上演示时如果模型 API 超时或额度用尽，这个模块要能顶上，
返回结构必须和 llm_agent.analyze 完全一致，只是 source 标成 rule_fallback。
"""

from typing import Any


def rule_based_advice(player_context: dict[str, Any]) -> dict[str, Any]:
    """基于简单阈值的建议，输出结构与 LLM 版本一致。

    待实现（D），建议规则示例（可自行调整，但必须写进
    docs/algorithm/pricing_model.md 或 docs/algorithm/ai_agent_prompt.md）：
    - 近 N 个价格点涨幅 > +5% 且评分 < 60  -> SELL，risk_level = HIGH
    - 近 N 个价格点跌幅 < -5% 且评分 >= 75 -> BUY，risk_level = MEDIUM
    - 其他情况                             -> HOLD，risk_level = LOW

    返回：
        {
          "player_id": ...,
          "action": "HOLD",
          "reason": "未检测到明显信号（规则版建议）",
          "risk_level": "LOW",
          "suggested_price_band": {...},
          "source": "rule_fallback",
          "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
        }
    """
    raise NotImplementedError("D 同学实现规则版降级建议")

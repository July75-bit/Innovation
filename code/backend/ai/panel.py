"""多角色协作：分析师 → 风控 → 交易员，产出一份"决策纪要"。

负责人：B

**为什么要三个角色而不是一次问答**：
单次问答里模型容易"一次性给结论"；拆成三个角色后，每一步只干一件事，
不仅能演示"多智能体协作"，还能暴露**分歧**——答辩时"风控不同意交易员的加仓"
比"AI 说 BUY"有价值得多。

**成本控制**：三次调用串行，最坏 3×超时；任一环节失败 → 整份纪要回落规则版
（`source=rule_fallback`），仍然 200，不影响交易。

**只读**：三个角色都只吃上下文、不写库；纪要由调用方决定是否落 trace。
"""

from __future__ import annotations

from typing import Any

from ai.fallback import rule_based_advice
from ai.llm_agent import _default_chat, analyze

ROLE_PROMPTS = {
    "analyst": (
        "你是行情分析师。只做一件事：根据给定的价格历史与表现评分，判断当前趋势"
        "（上行/下行/震荡）并给出 1–2 句依据。不要给买卖建议，不要编造数据。"
    ),
    "risk": (
        "你是风控官。只做一件事：根据账户余额、持仓与选手波动，指出这笔潜在交易的风险"
        "（资金占用、集中度、回撤幅度），并给出仓位上限建议（股数）。"
        "宁可保守，不要鼓励加仓。"
    ),
    "trader": (
        "你是交易员。根据分析师与风控的意见，给出最终动作（BUY/SELL/HOLD）、风险等级"
        "（LOW/MEDIUM/HIGH）与一句话理由。如果与风控意见冲突，必须明确指出冲突点。"
    ),
}


def _clip(text: str, limit: int = 220) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def run_panel(context: dict[str, Any], *, settings: Any = None) -> dict[str, Any]:
    """跑三角色流水线；返回 {source, minutes:[...], final:{...}}，失败自动降级。"""
    digest = (
        f"选手：{context.get('name')}（{context.get('team')}，评分 {context.get('rating')}）\n"
        f"现价 {context.get('current_price')}，近期变动 {context.get('change_pct')}%\n"
        f"最近价格点：{context.get('recent_prices')}\n"
        f"持仓：{context.get('position')}\n"
    )

    minutes: list[dict[str, str]] = []
    try:
        analyst = _default_chat(f"{digest}\n请按你的角色输出。", settings=settings)
        minutes.append({"role": "analyst", "content": _clip(analyst)})

        risk = _default_chat(
            f"{digest}\n分析师意见：{_clip(analyst)}\n请按风控角色输出。", settings=settings
        )
        minutes.append({"role": "risk", "content": _clip(risk)})

        trader = _default_chat(
            f"{digest}\n分析师：{_clip(analyst)}\n风控：{_clip(risk)}\n"
            "按交易员角色输出：动作 / 风险等级 / 一句话理由（可在末尾标注与风控的冲突）。",
            settings=settings,
        )
        minutes.append({"role": "trader", "content": _clip(trader)})

        advice = analyze(context, settings=settings)
        return {
            "source": "llm",
            "minutes": minutes,
            "final": {
                "action": advice.get("action"),
                "risk_level": advice.get("risk_level"),
                "reason": _clip(str(advice.get("reason")), 160),
                "disclaimer": advice.get("disclaimer"),
            },
            "note": "三个角色分别调用模型；最终动作以交易员环节为准，冲突点已写在纪要里",
        }
    except Exception as exc:  # noqa: BLE001 —— 任一环节失败整份回落规则版
        fallback = rule_based_advice(context)
        return {
            "source": "rule_fallback",
            "minutes": minutes
            + [{"role": "system", "content": f"多角色协作不可用（{type(exc).__name__}），已回落规则版"}],
            "final": {
                "action": fallback.get("action"),
                "risk_level": fallback.get("risk_level"),
                "reason": _clip(str(fallback.get("reason")), 160),
                "disclaimer": fallback.get("disclaimer"),
            },
            "note": "模型不可用时仍给出一致结构的纪要，接口 200",
        }

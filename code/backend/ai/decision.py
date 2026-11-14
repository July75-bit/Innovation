"""把"一条建议"翻译成"可执行的计划"（第 8 轮：决策卡）。

负责人：B

**为什么要把建议变成计划**：答辩评委看到的差别是——"AI 说 BUY" 是玩具，
"AI 说 BUY，建议 12 股、参考止损 108.4、置信度 0.72，并说明按你 5000 余额算的"才是产品。

**边界（一字不让）**：这里只做**算术**，不下单、不写任何业务表。
真正的下单仍要用户点"买入"走 `/api/trades/buy`（契约 §4.7），
所以"AI 不碰钱"这条在设计上没有被削弱。

算法要点（都可口头解释，不需要背参数）：
- **仓位**：按风险等级给"可动用的钱"上限（LOW 10% / MEDIUM 6% / HIGH 3%），
  再叠加三条硬约束：余额、单选手 50 股上限、持仓集中度（已持有就不再建议加）；
- **止损**：按风险等级给回撤线（LOW 12% / MEDIUM 9% / HIGH 6%），向下取整到分；
- **置信度**：来源（模型 > 规则）× 评分档位 × 波动惩罚，压到 0.35–0.92 区间，
  并**明确标注这是启发式**，不是概率校准过的模型输出。
"""

from __future__ import annotations

from decimal import Decimal

CENT = Decimal("0.01")

#: 风险等级 → (可动用余额比例, 止损回撤比例)
_RISK_PROFILE = {
    "LOW": (0.10, 0.12),
    "MEDIUM": (0.06, 0.09),
    "HIGH": (0.03, 0.06),
}


def _floor_money(value: float) -> float:
    return float(Decimal(str(value)).quantize(CENT))


def confidence_score(*, source: str, rating: int, change_pct: float) -> float:
    """启发式置信度（0.35–0.92）：模型 > 规则；高评分加分；大波动扣分。"""
    base = 0.70 if source == "llm" else 0.55
    rating_bonus = (min(max(rating, 0), 100) - 70) / 100 * 0.15  # ±0.045 左右
    volatility_penalty = min(abs(change_pct) / 100, 0.12)  # 跌/涨 20% 扣 0.024
    return round(min(0.92, max(0.35, base + rating_bonus - volatility_penalty)), 2)


def build_plan(
    advice: dict,
    *,
    balance: float,
    current_price: float,
    held_quantity: int = 0,
    position_limit: int = 50,
) -> dict:
    """由建议 + 账户状态算出计划；返回的每个字段都能被前端直接展示。"""
    action = str(advice.get("action", "HOLD")).upper()
    risk = str(advice.get("risk_level", "MEDIUM")).upper()
    source = str(advice.get("source", "rule_fallback"))
    rating = int(advice.get("_rating", 70) or 70)
    change_pct = float(advice.get("_change_pct", 0.0) or 0.0)

    budget_ratio, stop_ratio = _RISK_PROFILE.get(risk, _RISK_PROFILE["MEDIUM"])
    confidence = confidence_score(source=source, rating=rating, change_pct=change_pct)

    quantity = 0
    stop_loss: float | None = None
    rationale: list[str] = []

    if action == "BUY" and current_price > 0:
        affordable = int(balance // current_price) if balance > 0 else 0
        risk_budget = int((balance * budget_ratio) // current_price)
        room = max(0, position_limit - held_quantity)
        quantity = max(0, min(affordable, risk_budget, room))
        stop_loss = _floor_money(current_price * (1 - stop_ratio))
        rationale.append(f"可用 {balance:.2f} 币 × 风险预算 {int(budget_ratio * 100)}% → {risk_budget} 股")
        rationale.append(f"单选手上限 {position_limit} 股、已持 {held_quantity} 股 → 还能买 {room} 股")
        if held_quantity > 0:
            rationale.append("已持有该选手，本建议只做提示、不追加")
            quantity = min(quantity, 0)
        if quantity == 0:
            rationale.append("按当前约束不建议开新仓（余额/上限/已持有）")
    elif action == "SELL":
        quantity = int(held_quantity)
        rationale.append(f"当前持有 {held_quantity} 股，卖出建议按全部可卖计算")
        if held_quantity == 0:
            rationale.append("当前无持仓，卖出建议仅作行情提示")
    else:
        rationale.append("HOLD：不建议新增仓位，继续观察")
        if held_quantity:
            rationale.append(f"已有 {held_quantity} 股，止损参考 {_floor_money(current_price * (1 - stop_ratio)):.2f}")

    return {
        "suggested_quantity": int(quantity),
        "stop_loss_price": stop_loss,
        "confidence": confidence,
        "risk_budget_ratio": budget_ratio,
        "rationale": rationale,
        "note": "启发式估算（非模型概率）；下单仍需你本人确认",
    }

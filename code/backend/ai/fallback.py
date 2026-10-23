"""规则版降级建议（不依赖任何大模型）。

负责人：D

为什么需要它：课程材料把"AI 接口不稳定时系统仍能交易"列为硬要求。
第 5 天线上演示时如果模型 API 超时、额度用尽或未配置密钥，本模块顶上，
返回结构与 `llm_agent.analyze` 完全一致，只是 `source` 标成 `rule_fallback`。

口径说明（2026-10-23 与契约 §4.10 对齐）：
- 只读函数：不修改余额 / 持仓，不做任何数据库写入；
- 不输出 `suggested_price_band`（契约中该字段可缺省）：
  规则模型没有价格预测能力，不编造区间；前端按"可缺省"容错。
"""

from typing import Any

# ---------- 规则参数（改动必须同步 docs/algorithm/ai_agent_prompt.md §5）----------
WINDOW = 5              # 观察最近几个价格区间
RISE_THRESHOLD = 5.0    # 涨幅阈值（%）
FALL_THRESHOLD = -5.0   # 跌幅阈值（%）
LOW_RATING = 60         # 表现分低于此值：上涨缺乏支撑
HIGH_RATING = 75        # 表现分高于此值：下跌属错杀

DEFAULT_RATING = 50.0
MAX_REASON_LEN = 120

DISCLAIMER = "仅为分析建议，不构成投资建议；AI 不会自动交易"


def _num(value: Any, default: float | None = 0.0) -> float | None:
    """防御式取数：字段缺失 / None / 非数字都回落到 default，绝不抛异常。"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def window_change_pct(player_context: dict[str, Any]) -> tuple[float, int]:
    """取最近 WINDOW 个价格点的涨跌幅（%）。

    优先用 recent_prices 计算；不足 2 个有效点时回退到上下文里的 change_pct。
    返回 (涨跌幅, 参与计算的点数)。
    """
    raw = player_context.get("recent_prices") or []
    points: list[float] = []
    for item in raw:
        price = item.get("price") if isinstance(item, dict) else item
        value = _num(price, None)
        if value is not None and value > 0:
            points.append(value)

    if len(points) > WINDOW + 1:
        points = points[-(WINDOW + 1):]

    if len(points) >= 2:
        first, last = points[0], points[-1]
        return (last - first) / first * 100.0, len(points) - 1

    return _num(player_context.get("change_pct"), 0.0) or 0.0, len(points)


def rule_based_advice(player_context: dict[str, Any]) -> dict[str, Any]:
    """基于阈值的建议，输出结构与 LLM 版本一致（见契约 §4.10）。

    Args:
        player_context: B 组装的行情上下文，至少含 `player_id`；
            `current_price` / `rating` / `change_pct` / `recent_prices` / `position`
            缺失时按默认值处理，不抛异常。

    Returns:
        {
          "player_id": 1,
          "action": "BUY" | "SELL" | "HOLD",
          "reason": "≤120 字中文，引用具体数值",
          "risk_level": "LOW" | "MEDIUM" | "HIGH",
          "source": "rule_fallback",
          "disclaimer": "..."
        }

    规则（与 docs/algorithm/ai_agent_prompt.md §5 一致）：
        1. 近 N 点涨幅 > +5% 且 rating < 60            -> SELL / HIGH
        2. 近 N 点跌幅 < -5% 且 rating >= 75           -> BUY  / MEDIUM
        3. 命中 1 但当前持仓为 0                       -> HOLD / LOW（降级）
        4. 其他                                        -> HOLD / LOW
    """
    ctx = player_context or {}
    player_id = ctx.get("player_id")

    rating_raw = _num(ctx.get("rating"), DEFAULT_RATING)
    rating = DEFAULT_RATING if rating_raw is None else rating_raw
    pct, _ = window_change_pct(ctx)

    position = ctx.get("position") or {}
    held_raw = _num(position.get("quantity"), 0.0)
    held = 0.0 if held_raw is None else held_raw

    if pct > RISE_THRESHOLD and rating < LOW_RATING:
        action, risk = "SELL", "HIGH"
        reason = (
            f"近 {WINDOW} 个价格点累计上涨 {pct:+.1f}%，但综合表现分仅 {rating:.0f}，"
            f"上涨缺乏表现支撑（规则版建议）"
        )
    elif pct < FALL_THRESHOLD and rating >= HIGH_RATING:
        action, risk = "BUY", "MEDIUM"
        reason = (
            f"近 {WINDOW} 个价格点累计下跌 {pct:+.1f}%，但综合表现分仍有 {rating:.0f}，"
            f"回调后估值偏低（规则版建议）"
        )
    else:
        action, risk = "HOLD", "LOW"
        reason = (
            f"近 {WINDOW} 个价格点累计变动 {pct:+.1f}%，综合表现分 {rating:.0f}，"
            f"未触发买卖阈值（规则版建议）"
        )

    # 没有持仓却建议卖出，是做不到的动作 → 降级为 HOLD
    if action == "SELL" and held <= 0:
        action, risk = "HOLD", "LOW"
        reason = (
            f"价格虽累计上涨 {pct:+.1f}% 且表现分仅 {rating:.0f}，但当前无持仓，"
            f"卖出无实际意义，建议观望（规则版建议）"
        )

    return {
        "player_id": player_id,
        "action": action,
        "reason": reason[:MAX_REASON_LEN],
        "risk_level": risk,
        "source": "rule_fallback",
        "disclaimer": DISCLAIMER,
    }

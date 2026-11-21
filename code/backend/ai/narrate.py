"""价格变动的"叙事归因"：把 rule 式 reason 扩写成一段可读的因果解释。

负责人：B（接线） / C（价格与 reason 口径）

**为什么单独做**：`price_history.reason` 是**规则模板**（"本场表现下滑（本轮得分 78.1，
S=-0.68），价格下跌 10.12%"），信息准确但干巴。叙事归因在不改库的前提下，
为"大幅波动的那几个点"生成 2–3 句人话，并**缓存**（同一 `(player_id, ts)` 只生成一次）。

**成本控制**：只对 `|change_pct| >= BIG_MOVE_PCT` 的点生成；其余直接回规则 reason。
**缓存**：写 `price_narratives` 表（唯一键 player_id+ts），重复请求不再调模型。
**降级**：无密钥/超时 → 返回规则 reason 并标 `source=rule_fallback`，接口 200。
"""

from __future__ import annotations

import re
from typing import Any

from ai.llm_agent import _default_chat

BIG_MOVE_PCT = 8.0

NARRATIVE_PROMPT = (
    "你是行情解说。给定一位虚拟选手股票的价格点（含本轮比赛得分与规则归因），"
    "用 2–3 句中文解释这次涨跌的因果关系，要求：① 必须引用具体数字（价格、涨跌幅、得分）；"
    "② 不预测未来、不给买卖建议；③ 不超过 120 字。"
)


def is_big_move(change_pct: float) -> bool:
    return abs(float(change_pct or 0.0)) >= BIG_MOVE_PCT


def compose_narrative(points: list[dict[str, Any]]) -> str:
    """规则版兜底：把最近几个点拼成一句人话（不需要模型）。"""
    if not points:
        return "暂无足够的价格历史可供归因。"
    last = points[-1]
    prev = points[-2] if len(points) > 1 else None
    price = float(last.get("price") or 0)
    if prev:
        prev_price = float(prev.get("price") or 0)
        pct = (price - prev_price) / prev_price * 100 if prev_price else 0.0
        trend = "上涨" if pct > 0 else "下跌" if pct < 0 else "持平"
        head = f"最新价 {price:.2f}，较上一点{trend} {abs(pct):.2f}%。"
    else:
        head = f"最新价 {price:.2f}。"
    return f"{head}规则归因：{str(last.get('reason') or '').strip()}"


def generate_narrative(
    *, name: str, team: str, points: list[dict[str, Any]], settings: Any = None
) -> tuple[str, str, str]:
    """返回 (narrative, source, model_name)；失败时 source=rule_fallback。"""
    from ai.llm_agent import _model

    if not points:
        return compose_narrative(points), "rule_fallback", ""

    detail = "\n".join(
        f"- {p.get('ts')} 价格 {p.get('price')}｜{p.get('reason')}" for p in points[-4:]
    )
    prompt = (
        f"{NARRATIVE_PROMPT}\n\n选手：{name}（{team}）\n最近价格点：\n{detail}"
    )
    try:
        text = _clean_model_text(_default_chat(prompt, settings=settings))
        if not text:
            raise ValueError("模型返回空文本")
        return text[:400], "llm", _model(settings)
    except Exception:  # noqa: BLE001 —— 任何失败都回落规则版
        return compose_narrative(points), "rule_fallback", ""


#: 模型偶尔不按"说人话"来，直接把 JSON 吐出来（页面就会显示 {"action":"SELL",...}）
_JSON_KEY_RE = re.compile(r'"(?:reason|summary|text|narrative)"\s*:\s*"((?:[^"\\]|\\.)*)')


def _clean_model_text(raw: str) -> str:
    """把模型输出清洗成**一句人话**：剥代码围栏、若为 JSON 就取 reason/summary 字段。

    2026-11-14 用户截图发现：叙事归因位置直接显示了
    `{"action":"SELL","reason":"…","risk_level":"HIGH"}`，页面观感很差。
    这里统一兜底（与简报的 `_clean_brief_summary` 同一套路）：
    1. 去 markdown 围栏；
    2. 是 JSON → 正则取 reason/summary/text/narrative（截断的 JSON 也能救）；
    3. 取不到就剥掉花括号、引号与常见字段名，当纯文本用；
    4. 合并空白、去掉首尾空白。
    """
    text = (raw or "").strip()
    if not text:
        return ""

    text = re.sub(r"^```\w*\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    if text.startswith("{"):
        match = _JSON_KEY_RE.search(text)
        if match:
            text = match.group(1).replace('\\"', '"').replace("\\n", " ")
        else:
            text = re.sub(r'[{}"]', "", text)
            text = re.sub(r"\b(action|risk_level|reason|summary|text|narrative)\s*[:：]\s*", "", text)

    return re.sub(r"\s+", " ", text).strip()

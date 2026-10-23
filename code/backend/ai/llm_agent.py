"""LLM 调用封装。

负责人：D

对外入口：`analyze(player_context, *, chat=None, settings=None) -> dict`

- 有密钥：调模型 → 解析校验 → `source="llm"`
- 无密钥 / 调用失败 / 返回非法 JSON / 超时 / 模型输出不合规：**一律回落**
  `ai.fallback.rule_based_advice`，`source="rule_fallback"`

设计要点（对应 day2 计划与契约 §4.10）：

1. **`chat` 可注入**：`Callable[[str], str]`，收 user prompt、返回模型原始文本。
   注入后完全不需要网络和密钥 —— 单测与"无密钥演示"都靠它，这也是能验证降级链路的前提。
2. **默认客户端用标准库 `urllib`**，超时取 `settings.llm_timeout_seconds`（默认 20s）。
   不用 httpx 的理由：少一个运行时依赖，且在没有网络的机器上也能真实跑通"调用失败 → 回落"分支。
3. **输出固定 6 个字段，不含 `suggested_price_band`**
   （2026-10-23 决策：两版字段集合完全一致；规则版不编造区间，契约中该字段可缺省）。
4. **只读**：不写数据库、不改余额/持仓。
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

try:  # 正常以包方式导入
    from ai.fallback import DISCLAIMER, rule_based_advice
    from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
except ImportError:  # 允许在 ai/ 目录内直接运行脚本
    from fallback import DISCLAIMER, rule_based_advice
    from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# ---------- 常量 ----------
DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 20.0
MAX_REASON_LEN = 120

VALID_ACTIONS = {"BUY", "SELL", "HOLD"}
VALID_RISKS = {"LOW", "MEDIUM", "HIGH"}

ACTION_ALIASES = {
    "BUY": "BUY", "SELL": "SELL", "HOLD": "HOLD",
    "买入": "BUY", "买": "BUY", "看多": "BUY",
    "卖出": "SELL", "卖": "SELL", "看空": "SELL",
    "持有": "HOLD", "观望": "HOLD", "中性": "HOLD",
}
RISK_ALIASES = {
    "LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH",
    "低": "LOW", "低风险": "LOW",
    "中": "MEDIUM", "中风险": "MEDIUM",
    "高": "HIGH", "高风险": "HIGH",
}

# 输出的字段集合（两版必须完全一致）
OUTPUT_KEYS = ("player_id", "action", "reason", "risk_level", "source", "disclaimer")

ChatFn = Callable[[str], str]


class LLMOutputError(ValueError):
    """模型输出不可用（非 JSON / 枚举非法 / 缺理由 / 响应结构异常）。"""


# ---------- 配置读取（本地无 pydantic-settings 时也能工作）----------

def _load_settings() -> Any:
    try:
        from app.core.config import settings

        return settings
    except Exception:
        return None


def _api_key(settings: Any) -> str:
    if settings is not None and getattr(settings, "llm_api_key", ""):
        return str(settings.llm_api_key)
    return os.getenv("LLM_API_KEY", "")


def _model(settings: Any) -> str:
    if settings is not None and getattr(settings, "llm_model", ""):
        return str(settings.llm_model)
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def _timeout(settings: Any) -> float:
    if settings is not None and getattr(settings, "llm_timeout_seconds", None):
        return float(settings.llm_timeout_seconds)
    return float(os.getenv("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT))


def _base_url() -> str:
    return os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)


# ---------- prompt 组装 ----------

class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # 字段缺失时不抛 KeyError
        return "（缺失）"


def _fmt_prices(prices: Any) -> str:
    if not isinstance(prices, list) or not prices:
        return "（无价格历史）"
    parts = []
    for item in prices[-8:]:
        if isinstance(item, dict):
            parts.append(f"{item.get('price')}@{item.get('ts', '')}".rstrip("@"))
        else:
            parts.append(str(item))
    return " → ".join(parts)


def _fmt_position(position: Any) -> str:
    if not isinstance(position, dict):
        return "（无持仓）"
    quantity = position.get("quantity", 0) or 0
    if not quantity:
        return "无持仓"
    return f"持有 {quantity} 股，买入均价 {position.get('avg_cost', 0)}"


def build_user_prompt(player_context: dict[str, Any]) -> str:
    ctx = player_context or {}
    values = _SafeDict(
        name=ctx.get("name", "（未知）"),
        display_name=ctx.get("display_name") or "",
        team=ctx.get("team") or "（未知）",
        role=ctx.get("role") or "（未知）",
        player_id=ctx.get("player_id"),
        current_price=ctx.get("current_price"),
        change_pct=ctx.get("change_pct"),
        rating=ctx.get("rating"),
        recent_prices=_fmt_prices(ctx.get("recent_prices")),
        recent_reasons="；".join(ctx.get("recent_reasons") or []) or "（无）",
        position=_fmt_position(ctx.get("position")),
    )
    return USER_PROMPT_TEMPLATE.format_map(values)


# ---------- 默认客户端（标准库，无第三方依赖）----------

def _default_chat(user_prompt: str, *, settings: Any = None) -> str:
    """调用 OpenAI 兼容的 chat/completions 接口，返回模型原始文本。

    无网络 / 超时 / 非 2xx / 响应结构异常 都抛 LLMOutputError，由 analyze 回落。
    """
    import urllib.error
    import urllib.request

    api_key = _api_key(settings)
    if not api_key:
        raise LLMOutputError("未配置 LLM_API_KEY")

    payload = {
        "model": _model(settings),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        _base_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_timeout(settings)) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # URLError / HTTPError / TimeoutError / 非 JSON 响应
        raise LLMOutputError(f"模型调用失败：{type(exc).__name__}: {exc}") from exc

    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMOutputError("模型响应结构异常（缺少 choices[0].message.content）") from exc


# ---------- 解析与校验 ----------

def _extract_json_object(raw: str) -> dict[str, Any]:
    """从模型原始文本里抽出第一个 JSON 对象（容忍 ```json 包裹与前后废话）。"""
    if not isinstance(raw, str) or not raw.strip():
        raise LLMOutputError("模型返回空内容")

    text = raw.strip()
    if text.startswith("```"):
        # 去掉代码围栏：```json ... ```
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMOutputError("模型输出里找不到 JSON 对象")

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"JSON 解析失败：{exc}") from exc
    if not isinstance(parsed, dict):
        raise LLMOutputError("JSON 顶层不是对象")
    return parsed


def _normalize_enum(value: Any, aliases: dict[str, str], field: str) -> str:
    if not isinstance(value, str):
        raise LLMOutputError(f"{field} 不是字符串：{value!r}")
    key = value.strip().strip("“”\"'").upper()
    if key in aliases:
        return aliases[key]
    stripped = value.strip()
    if stripped in aliases:
        return aliases[stripped]
    raise LLMOutputError(f"{field} 取值非法：{value!r}")


def _parse_and_validate(raw: str) -> dict[str, str]:
    """解析模型输出并做结构校验，返回 {action, reason, risk_level}。

    非法输入统一抛 LLMOutputError（由 analyze 捕获后回落规则版）。
    额外字段（含 suggested_price_band）一律丢弃，保证两版字段集合一致。
    """
    parsed = _extract_json_object(raw)

    action = _normalize_enum(parsed.get("action"), ACTION_ALIASES, "action")
    risk_level = _normalize_enum(parsed.get("risk_level"), RISK_ALIASES, "risk_level")

    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise LLMOutputError("reason 缺失或为空")
    reason = reason.strip()
    if len(reason) > MAX_REASON_LEN:
        reason = reason[:MAX_REASON_LEN]

    return {"action": action, "reason": reason, "risk_level": risk_level}


# ---------- 对外入口 ----------

def _fallback(player_context: dict[str, Any]) -> dict[str, Any]:
    """规则版兜底，并保证字段集合与 LLM 版一致。"""
    advice = rule_based_advice(player_context or {})
    advice.pop("suggested_price_band", None)  # 契约允许缺省；本课程版本统一不输出
    return {key: advice.get(key) for key in OUTPUT_KEYS}


def analyze(
    player_context: dict[str, Any],
    *,
    chat: ChatFn | None = None,
    settings: Any = None,
) -> dict[str, Any]:
    """分析单个选手并给出交易建议（永不抛异常）。

    Args:
        player_context: `ai.context.build_player_context()` 的产物（或缺字段的字典）。
        chat: 可注入的模型调用函数，签名 `(user_prompt) -> 原始文本`。
            传入后不再需要密钥与网络（单测/演示用）。
            默认使用标准库 urllib 直连 OpenAI 兼容接口。
        settings: 可注入的配置对象（测试用）；默认读取 `app.core.config.settings`。

    Returns:
        固定 6 个字段：player_id / action / reason / risk_level / source / disclaimer
    """
    context = player_context or {}
    resolved = settings if settings is not None else _load_settings()

    # 无密钥且没有注入客户端 → 直接规则版，连网络都不碰
    if chat is None and not _api_key(resolved):
        return _fallback(context)

    try:
        caller: ChatFn = chat if chat is not None else (lambda prompt: _default_chat(prompt, settings=resolved))
        raw = caller(build_user_prompt(context))
        parsed = _parse_and_validate(raw)
    except Exception:
        # 超时 / 网络错误 / 非 JSON / 枚举非法 / 缺字段 全部走这里
        return _fallback(context)

    return {
        "player_id": context.get("player_id"),
        "action": parsed["action"],
        "reason": parsed["reason"],
        "risk_level": parsed["risk_level"],
        "source": "llm",
        "disclaimer": DISCLAIMER,
    }


# ---------- 命令行演示（满足 T2-08 "命令行能输出 JSON"）----------

class _NoKeySettings:
    """强制走回落路径的假配置（演示/排查用）。"""

    llm_api_key = ""
    llm_model = DEFAULT_MODEL
    llm_timeout_seconds = DEFAULT_TIMEOUT
    llm_provider = "openai"


def _demo_clean_chat(prompt: str) -> str:
    return json.dumps(
        {
            "action": "BUY",
            "reason": "近 3 个价格点由 120.0 升至 126.0（+5.0%），综合表现分 88，估值仍偏低",
            "risk_level": "MEDIUM",
        },
        ensure_ascii=False,
    )


def _demo_dirty_chat(prompt: str) -> str:
    return "我觉得这只票不错，建议买入，理由是很强。（这里故意返回非 JSON）"


def _main(argv: list[str] | None = None) -> int:
    import argparse

    from ai.context import build_player_context

    parser = argparse.ArgumentParser(description="AI 分析命令行演示（输出结构化 JSON）")
    parser.add_argument("player_id", nargs="?", type=int, default=1)
    parser.add_argument(
        "--demo",
        choices=["auto", "llm", "dirty", "no-key"],
        default="auto",
        help="auto=按真实配置；llm=假 client 正常输出；dirty=假 client 脏输出；no-key=强制规则版",
    )
    args = parser.parse_args(argv)

    context = build_player_context(args.player_id)
    if args.demo == "llm":
        result = analyze(context, chat=_demo_clean_chat)
    elif args.demo == "dirty":
        result = analyze(context, chat=_demo_dirty_chat)
    elif args.demo == "no-key":
        result = analyze(context, settings=_NoKeySettings())
    else:
        result = analyze(context)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

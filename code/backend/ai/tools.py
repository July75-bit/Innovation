"""工具调用（tool use）：让模型自己决定"查什么"，而不是把上下文一次性灌进去。

负责人：B

**和现在单次问答的区别**：
- 现在：`build_player_context` → 拼成一大段 user prompt → 模型一次性给结论；
- 这里：给模型三个**只读工具**，它先要数据（查价格历史 / 查账户 / 算仓位）、
  读完再下结论。答辩时能演示"模型自己发起了 2 次查询"。

**工具都是只读的**（查库 + 纯算术），没有任何交易能力——与"AI 不碰钱"一致。
`executor` 由 API 层注入（`ai/` 不直接依赖 SQLAlchemy 会话），这样单测能塞假执行器。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from ai.llm_agent import _api_key, _base_url, _model, _timeout

ToolExecutor = Callable[[dict[str, Any]], Any]

MAX_TOOL_ROUNDS = 3

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "读取某位选手最近 N 个价格点（含每点原因），用于判断趋势。",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer", "description": "选手 id"},
                    "limit": {"type": "integer", "description": "取最近几个点，默认 6，最多 12"},
                },
                "required": ["player_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_account_snapshot",
            "description": "读取当前用户余额、持有该选手的股数与均价（只读）。",
            "parameters": {
                "type": "object",
                "properties": {"player_id": {"type": "integer"}},
                "required": ["player_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calc_position_size",
            "description": "按余额、风险等级、单价算建议股数（纯算术，不会下单）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "balance": {"type": "number"},
                    "price": {"type": "number"},
                    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    "held_quantity": {"type": "integer"},
                },
                "required": ["balance", "price", "risk_level"],
            },
        },
    },
]


class ToolLoopError(RuntimeError):
    """工具循环失败（网络/超时/协议不支持）——调用方应回落规则版。"""


def _post(messages: list[dict[str, Any]], tools: list[dict[str, Any]], *, settings: Any) -> dict:
    api_key = _api_key(settings)
    if not api_key:
        raise ToolLoopError("未配置 LLM_API_KEY")
    payload = {
        "model": _model(settings),
        "temperature": 0,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    req = urllib.request.Request(
        _base_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "playerstock-backend/1.0 (+course project; urllib)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_timeout(settings)) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise ToolLoopError(f"{type(exc).__name__}: {exc}") from exc


def run_tool_loop(
    system_prompt: str,
    user_prompt: str,
    executors: dict[str, ToolExecutor],
    *,
    settings: Any = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> dict[str, Any]:
    """跑一次带工具的对话，返回 {"content": str, "tool_calls": [...], "rounds": N}。"""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    trace: list[dict[str, Any]] = []

    for round_no in range(1, max_rounds + 1):
        body = _post(messages, TOOL_SPECS, settings=settings)
        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ToolLoopError("模型响应结构异常（缺少 choices[0].message）") from exc

        calls = message.get("tool_calls") or []
        if not calls:
            return {"content": str(message.get("content") or ""), "tool_calls": trace, "rounds": round_no}

        messages.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        for call in calls:
            fn = (call.get("function") or {})
            name = str(fn.get("name") or "")
            raw_args = fn.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            except ValueError:
                args = {}
            executor = executors.get(name)
            try:
                result = executor(args) if executor else {"error": f"未知工具 {name}"}
            except Exception as exc:  # noqa: BLE001 —— 工具失败不能让整轮崩掉
                result = {"error": f"{type(exc).__name__}: {exc}"}
            trace.append({"round": round_no, "name": name, "args": args, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id") or f"call_{len(trace)}",
                    "content": json.dumps(result, ensure_ascii=False)[:2000],
                }
            )

    raise ToolLoopError(f"工具调用超过 {max_rounds} 轮仍未给出结论")

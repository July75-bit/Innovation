"""ai/tools.py 工具循环 + LLM 端点读取的单测（离线，不联网）。

覆盖此前没测到的分支：多轮工具调用、未知工具、工具抛错、参数非 JSON、
超过轮数上限、响应结构异常、无密钥、网络失败；以及 `.env` 里的 LLM_BASE_URL
经 Settings 字段生效（2026-11-26 复现的回落问题）。
"""

from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

import ai.tools as tools
from ai.llm_agent import DEFAULT_BASE_URL, _base_url


def _reply(content: str | None = None, calls: list[dict] | None = None) -> dict:
    message: dict = {"content": content}
    if calls is not None:
        message["tool_calls"] = calls
    return {"choices": [{"message": message}]}


def _call(name: str, args: object, call_id: str | None = "c1") -> dict:
    raw = args if isinstance(args, str) else json.dumps(args)
    return {"id": call_id, "function": {"name": name, "arguments": raw}}


def _scripted(monkeypatch, replies: list[dict]) -> list[list[dict]]:
    """让 _post 按顺序返回预设响应，并记下每轮发出去的 messages。"""
    sent: list[list[dict]] = []
    queue = list(replies)

    def fake_post(messages, specs, *, settings):
        sent.append(list(messages))
        return queue.pop(0)

    monkeypatch.setattr(tools, "_post", fake_post)
    return sent


def test_returns_content_directly_when_no_tool_calls(monkeypatch):
    _scripted(monkeypatch, [_reply("直接给结论")])
    out = tools.run_tool_loop("sys", "user", {})
    assert out == {"content": "直接给结论", "tool_calls": [], "rounds": 1}


def test_runs_tools_then_answers(monkeypatch):
    sent = _scripted(
        monkeypatch,
        [
            _reply(calls=[_call("get_price_history", {"player_id": 3, "limit": 4})]),
            _reply("看完历史，建议观望"),
        ],
    )
    seen: list[dict] = []

    def history(args):
        seen.append(args)
        return {"points": [1, 2, 3]}

    out = tools.run_tool_loop("sys", "user", {"get_price_history": history})

    assert out["rounds"] == 2
    assert out["content"] == "看完历史，建议观望"
    assert seen == [{"player_id": 3, "limit": 4}]
    assert out["tool_calls"][0]["result"] == {"points": [1, 2, 3]}
    # 第二轮请求里要带上 assistant 的 tool_calls 和对应的 tool 结果
    roles = [m["role"] for m in sent[1]]
    assert roles == ["system", "user", "assistant", "tool"]
    assert sent[1][-1]["tool_call_id"] == "c1"


def test_unknown_tool_bad_args_and_failing_tool_do_not_crash(monkeypatch):
    def boom(_args):
        raise RuntimeError("库挂了")

    _scripted(
        monkeypatch,
        [
            _reply(
                calls=[
                    _call("no_such_tool", {}),
                    _call("calc_position_size", "{不是 JSON", call_id=None),
                    _call("get_account_snapshot", {"player_id": 1}),
                ]
            ),
            _reply("结论"),
        ],
    )
    out = tools.run_tool_loop(
        "sys",
        "user",
        {"calc_position_size": lambda args: {"args": args}, "get_account_snapshot": boom},
    )

    results = [c["result"] for c in out["tool_calls"]]
    assert results[0] == {"error": "未知工具 no_such_tool"}
    assert results[1] == {"args": {}}  # 参数解析失败按空参数处理
    assert results[2] == {"error": "RuntimeError: 库挂了"}


def test_raises_after_max_rounds(monkeypatch):
    _scripted(monkeypatch, [_reply(calls=[_call("x", {})]) for _ in range(2)])
    with pytest.raises(tools.ToolLoopError, match="超过 2 轮"):
        tools.run_tool_loop("sys", "user", {}, max_rounds=2)


def test_malformed_response_raises(monkeypatch):
    _scripted(monkeypatch, [{"choices": []}])
    with pytest.raises(tools.ToolLoopError, match="响应结构异常"):
        tools.run_tool_loop("sys", "user", {})


def test_post_without_key_raises():
    settings = SimpleNamespace(llm_api_key="", llm_model="m", llm_timeout_seconds=1)
    with pytest.raises(tools.ToolLoopError, match="LLM_API_KEY"):
        tools._post([], [], settings=settings)


def test_post_sends_request_to_configured_endpoint(monkeypatch):
    captured: dict = {}

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Resp(json.dumps(_reply("ok")).encode("utf-8"))

    monkeypatch.setattr(tools.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    settings = SimpleNamespace(
        llm_api_key="sk-x",
        llm_model="deepseek-flash",
        llm_timeout_seconds=7,
        llm_base_url="https://api.deepseek.com/v1",
    )
    body = tools._post([{"role": "user", "content": "hi"}], tools.TOOL_SPECS, settings=settings)

    assert body == _reply("ok")
    assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert captured["body"]["model"] == "deepseek-flash"
    assert captured["body"]["tools"] == tools.TOOL_SPECS
    assert captured["timeout"] == 7.0


def test_post_wraps_network_error(monkeypatch):
    def fail(req, timeout):
        raise OSError("连接被拒绝")

    monkeypatch.setattr(tools.urllib.request, "urlopen", fail)
    settings = SimpleNamespace(llm_api_key="sk-x", llm_model="m", llm_timeout_seconds=1)
    with pytest.raises(tools.ToolLoopError, match="OSError"):
        tools._post([], [], settings=settings)


# ---------- LLM_BASE_URL：Settings 字段优先于环境变量 ----------


def test_base_url_prefers_settings_field(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://env.example/v1")
    settings = SimpleNamespace(llm_base_url=' "https://api.deepseek.com/v1/" ')
    assert _base_url(settings) == "https://api.deepseek.com/v1/chat/completions"


def test_base_url_falls_back_to_env_then_default(monkeypatch):
    empty = SimpleNamespace(llm_base_url="")
    monkeypatch.setenv("LLM_BASE_URL", "https://env.example/v1")
    assert _base_url(empty) == "https://env.example/v1/chat/completions"
    monkeypatch.delenv("LLM_BASE_URL")
    assert _base_url(empty) == DEFAULT_BASE_URL


def test_dotenv_base_url_reaches_request(tmp_path, monkeypatch):
    """复现：只在 .env 里写 LLM_BASE_URL，以前会被忽略、请求打到 OpenAI 默认端点。"""
    from app.core.config import Settings

    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_MODEL=deepseek-flash\nLLM_BASE_URL=https://api.deepseek.com/v1\nLLM_API_KEY=sk-test\n",
        encoding="utf-8",
    )
    settings = Settings(_env_file=env_file)
    assert _base_url(settings) == "https://api.deepseek.com/v1/chat/completions"

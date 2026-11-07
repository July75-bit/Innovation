"""CORS 来源策略的测试（第 5 天 B 的决策，见 `deployment.md` §6 / `compliance.md` §4）。

依据 `docs/requirements/nonfunctional_spec.md` 的 **NFR-S-04**：
"部署后仅开放必要 CORS 来源，不使用 `allow_origins=["*"]`"。

策略（`app.main.resolve_cors_origins`）：
1. `CORS_ORIGINS` 配了具体域名 → 白名单（默认路径）；
2. 显式写 `*` → 放行全部，并打 WARNING；
3. 没配（空）→ 退化为 `*` 保演示可用，并打 WARNING（运维兜底，不是设计默认值）。

这三条以前都没测，线上那次 `allow_origins=["*"]` 硬编码就是"没人盯"的结果；
把行为钉住，以后改 CORS 必须先改这里。
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app import main as app_main


def _fake_settings(origins: list[str]) -> SimpleNamespace:
    return SimpleNamespace(cors_origin_list=origins)


def test_whitelist_is_used_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    frontend = "https://playerstock-frontend-mdlk.onrender.com"
    monkeypatch.setattr(app_main, "settings", _fake_settings([frontend]))

    assert app_main.resolve_cors_origins() == [frontend]


def test_explicit_wildcard_is_honoured_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(app_main, "settings", _fake_settings(["*"]))

    with caplog.at_level(logging.WARNING):
        assert app_main.resolve_cors_origins() == ["*"]

    assert "放行全部来源" in caplog.text


def test_empty_config_falls_back_to_wildcard_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """没配 CORS_ORIGINS 时不能静默白屏，也不能静默放开——放开但喊出来。"""
    monkeypatch.setattr(app_main, "settings", _fake_settings([]))

    with caplog.at_level(logging.WARNING):
        assert app_main.resolve_cors_origins() == ["*"]

    assert "CORS_ORIGINS 未配置" in caplog.text


def test_default_settings_only_allow_local_dev_origins() -> None:
    """默认配置（没设环境变量）必须是本地开发地址，不能是 `*`。"""
    from app.core.config import Settings

    origins = Settings().cors_origin_list

    assert "*" not in origins
    assert any("localhost" in origin or "127.0.0.1" in origin for origin in origins)


def test_trailing_slash_is_stripped() -> None:
    """控制台里手填成 `https://x.onrender.com/` 时也要能匹配（浏览器 Origin 不带尾斜杠）。"""
    from app.core.config import Settings

    origins = Settings(cors_origins="https://a.example.com/, https://b.example.com/").cors_origin_list

    assert origins == ["https://a.example.com", "https://b.example.com"]


def test_render_with_default_dev_origins_falls_back_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """线上却还是本地默认值 = 忘配了：退化放开 + 告警，绝不能让前端静默跨域失败。

    这是 2026-10-25 线上事故的回归用例：后端换成配置驱动后，
    Render 上的 `CORS_ORIGINS` 没填 → 只放行 localhost → 线上前端被拦。
    """
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(
        app_main, "settings", _fake_settings(["http://localhost:5173", "http://127.0.0.1:5173"])
    )

    with caplog.at_level(logging.WARNING):
        assert app_main.resolve_cors_origins() == ["*"]

    assert "仍是本地默认值" in caplog.text


def test_render_with_real_frontend_origin_uses_whitelist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """线上配了真实前端域名 → 走白名单（才是合规期望的路径）。"""
    monkeypatch.setenv("RENDER", "true")
    frontend = "https://playerstock-frontend-mdlk.onrender.com"
    monkeypatch.setattr(app_main, "settings", _fake_settings([frontend]))

    assert app_main.resolve_cors_origins() == [frontend]


def test_local_run_keeps_local_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    """本地没设 RENDER 时不该退化：localhost 白名单照常生效。"""
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(
        app_main, "settings", _fake_settings(["http://localhost:5173", "http://127.0.0.1:5173"])
    )

    assert app_main.resolve_cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]

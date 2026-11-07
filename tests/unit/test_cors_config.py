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

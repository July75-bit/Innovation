"""数据库连接串归一化的测试（部署预检发现的两个坑）。

负责人：B

第 4 天部署预检实测到的问题：Render 给的连接串是 `postgres://...`，而
**SQLAlchemy 2.1 起把 `postgresql://` 的默认驱动从 psycopg2 换成了 psycopg 3**，
本项目只装了 `psycopg2-binary`——不显式写驱动，线上启动就会
`ModuleNotFoundError: No module named 'psycopg'`。这两条测试把行为钉死。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.core.config import Settings


def _url(value: str) -> str:
    return Settings(database_url=value).database_url


@pytest.mark.parametrize(
    "raw",
    [
        "postgres://user:pw@dpg-xxxxx-a.singapore-postgres.render.com/playerstock_db",
        "postgresql://user:pw@dpg-xxxxx-a.singapore-postgres.render.com/playerstock_db",
    ],
)
def test_bare_postgres_urls_get_psycopg2_driver(raw: str) -> None:
    """裸 postgres:// 与 postgresql:// 都要补成 postgresql+psycopg2://。"""
    normalized = _url(raw)

    assert normalized.startswith("postgresql+psycopg2://")
    assert "postgres://" not in normalized
    # 用户名/密码/库名原样保留
    assert normalized.endswith("/playerstock_db")
    assert "user:pw@" in normalized


def test_explicit_driver_is_kept() -> None:
    """显式写了驱动的连接串不要改（例如想换 asyncpg / psycopg3）。"""
    for raw in (
        "postgresql+psycopg://user:pw@h/db",
        "postgresql+asyncpg://user:pw@h/db",
        "postgresql+psycopg2://user:pw@h/db",
    ):
        assert _url(raw) == raw


def test_render_postgres_url_builds_a_psycopg2_engine() -> None:
    """真正构造引擎：这是部署时最先炸的一步，必须解析到 psycopg2。"""
    engine = create_engine(_url("postgres://user:pw@dpg-xxxxx-a/db"))
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg2"
    finally:
        engine.dispose()


def test_sqlite_relative_path_resolves_under_backend_dir() -> None:
    """SQLite 相对路径统一相对 code/backend，避免 seed 与服务各用一个库。"""
    normalized = _url("sqlite:///./playerstock.db")

    assert normalized.startswith("sqlite:///")
    assert normalized.endswith("code/backend/playerstock.db")
    assert Path(normalized[len("sqlite:///") :]).is_absolute()


def test_memory_sqlite_is_not_rewritten() -> None:
    assert _url("sqlite:///:memory:") == "sqlite:///:memory:"

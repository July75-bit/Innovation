"""基础设施守卫：SQLite PRAGMA、会话生命周期、启动日志、演示账户自建。

为什么单独一个文件：这些是"跑起来之前"和"请求之外"的代码——
PRAGMA 没开就没有外键约束、会话没关就泄漏连接、启动日志不打就查不出
"线上为什么用错库"。正常业务用例覆盖不到它们，但它们是故障排查的第一现场。

不修改 `app/core/database.py` / `app/main.py` / `app/api/deps.py` 一行代码。
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, delete, inspect
from sqlalchemy.orm import Session

from app.api.deps import DEMO_NICKNAME, get_current_user
from app.core import database
from app.models import User


# ---------------------------------------------------------------- SQLite PRAGMA

class _FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.closed = False

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def close(self) -> None:
        self.closed = True


class _FakeConnection:
    def __init__(self) -> None:
        self._cursor = _FakeCursor()

    def cursor(self) -> _FakeCursor:
        return self._cursor


def test_sqlite_pragmas_enable_foreign_keys_and_wal() -> None:
    """三条 PRAGMA 一个都不能少：外键、忙等超时、WAL 日志模式。"""
    conn = _FakeConnection()

    database._sqlite_pragmas(conn, None)  # type: ignore[arg-type]

    executed = " | ".join(conn._cursor.executed)
    assert "PRAGMA foreign_keys=ON" in executed
    assert "PRAGMA busy_timeout=5000" in executed
    assert "PRAGMA journal_mode=WAL" in executed
    assert conn._cursor.closed, "游标用完必须关闭，否则连接会泄漏"


# ---------------------------------------------------------------- 会话生命周期

def test_get_db_yields_session_and_closes_on_exit() -> None:
    gen = database.get_db()
    session = next(gen)
    assert isinstance(session, Session)

    with pytest.raises(StopIteration):
        next(gen)  # 触发 finally：会话关闭


# ---------------------------------------------------------------- 建表

def test_init_db_creates_all_tables(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init_db 要在给定引擎上建出 5 张表（本地开发/CI 的建库入口）。"""
    temp_engine = create_engine(f"sqlite:///{(tmp_path / 'init.db').as_posix()}")
    monkeypatch.setattr(database, "engine", temp_engine)

    database.init_db()

    tables = set(inspect(temp_engine).get_table_names())
    assert {"users", "players", "positions", "trades", "price_history"} <= tables
    temp_engine.dispose()


# ---------------------------------------------------------------- 启动生命周期

def test_lifespan_logs_database_and_warns_when_render_uses_sqlite(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """RENDER 环境下仍用 SQLite 必须打 WARNING——这是"数据总是丢"的排查入口。"""
    from fastapi.testclient import TestClient

    from app.main import app as fastapi_app

    monkeypatch.setattr("app.main.init_db", lambda: None)  # 不碰真实库
    monkeypatch.setenv("RENDER", "1")

    with caplog.at_level("WARNING"):
        with TestClient(fastapi_app) as test_client:
            assert test_client.get("/api/health").status_code == 200

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "SQLite" in messages
    assert "数据会全部丢失" in messages


# ---------------------------------------------------------------- 演示账户自建

def test_get_current_user_creates_demo_account_when_missing(session_factory) -> None:
    """首次请求（库里没有 demo 账户）应按 initial_balance 自动开户。"""
    with session_factory() as db:
        db.execute(delete(User))
        db.commit()

        user = get_current_user(db=db)

        assert user.nickname == DEMO_NICKNAME
        assert Decimal(user.balance) == Decimal("5000.00")
        assert Decimal(user.initial_balance) == Decimal("5000.00")

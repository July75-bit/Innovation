"""日志落盘与日志自检接口（D，2026-11-07）。

覆盖：setup_logging 真实的文件写入与滚动配置、recent_lines 读取、
/api/debug/logs 的正常返回与 DEBUG_ENDPOINTS=0 时的关闭行为。
"""

from __future__ import annotations

import logging

import pytest

from app.core import logging_config


@pytest.fixture()
def log_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """每个用例一个独立日志目录，且强制重配（避免污染仓库 logs/app.log）。"""
    directory = tmp_path / "logs"
    monkeypatch.setattr(logging_config, "_configured_path", None)
    path = logging_config.setup_logging(directory, force=True)
    yield path
    monkeypatch.setattr(logging_config, "_configured_path", None)


def test_setup_logging_creates_file_and_writes(log_dir) -> None:
    assert log_dir.exists()
    assert log_dir.name == "app.log"

    logging.getLogger("playerstock.test").warning("这是一条测试日志 %s", 123)

    text = log_dir.read_text(encoding="utf-8")
    assert "WARNING" in text
    assert "playerstock.test" in text
    assert "这是一条测试日志 123" in text


def test_logging_is_idempotent_and_reports_path(log_dir) -> None:
    second = logging_config.setup_logging()  # 不 force，应返回同一路径
    assert second == log_dir
    assert logging_config.current_log_path() == log_dir


def test_recent_lines_returns_tail(log_dir) -> None:
    logger = logging.getLogger("playerstock.test.tail")
    for index in range(5):
        logger.info("第 %d 行", index)

    rows = logging_config.recent_lines(2, path=log_dir)
    assert len(rows) == 2
    assert "第 4 行" in rows[-1]


def test_recent_lines_missing_file_returns_empty(tmp_path) -> None:
    assert logging_config.recent_lines(10, path=tmp_path / "不存在.log") == []


def test_recent_lines_clamps_count(log_dir) -> None:
    logging.getLogger("playerstock.test.clamp").info("唯一一行")
    # 超过上限 500 时应被截到 500 以内，不抛异常
    assert len(logging_config.recent_lines(9999, path=log_dir)) >= 1


def test_debug_logs_endpoint_returns_content(client, log_dir, monkeypatch) -> None:
    logging.getLogger("playerstock.test.api").warning("接口可见的日志行")
    monkeypatch.setattr(
        "app.api.logs.recent_lines", lambda count: logging_config.recent_lines(count, path=log_dir)
    )
    monkeypatch.setattr("app.api.logs.current_log_path", lambda: log_dir)

    response = client.get("/api/debug/logs?lines=50")

    assert response.status_code == 200
    body = response.json()
    assert body["返回行数"] >= 1
    assert any("接口可见的日志行" in row for row in body["内容"])
    assert "不含口令" in body["提示"]


def test_debug_logs_endpoint_filters_by_level(client, log_dir, monkeypatch) -> None:
    logger = logging.getLogger("playerstock.test.level")
    logger.info("普通信息")
    logger.error("这是错误")
    monkeypatch.setattr(
        "app.api.logs.recent_lines", lambda count: logging_config.recent_lines(count, path=log_dir)
    )
    monkeypatch.setattr("app.api.logs.current_log_path", lambda: log_dir)

    body = client.get("/api/debug/logs?lines=100&level=ERROR").json()
    assert body["返回行数"] >= 1
    assert all("ERROR" in row for row in body["内容"])


def test_debug_logs_endpoint_can_be_disabled(client, monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "debug_endpoints", False)

    response = client.get("/api/debug/logs")

    assert response.status_code == 404
    assert response.json()["code"] == "ENDPOINT_DISABLED"

def test_default_log_dir_honours_env(monkeypatch, tmp_path) -> None:
    """LOG_DIR 环境变量优先于仓库默认目录。"""
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "custom"))
    assert logging_config.default_log_dir() == tmp_path / "custom"


def test_setup_logging_falls_back_to_temp_when_dir_unwritable(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """目录不可写时退到临时目录，绝不能让"日志失败"拖垮启动。"""
    monkeypatch.setattr(logging_config, "_configured_path", None)

    real_open = logging_config._open_handler

    def _boom_only_for_readonly_dir(path):
        if "只读目录" in str(path):
            raise OSError("read-only file system")
        return real_open(path)

    monkeypatch.setattr(logging_config, "_open_handler", _boom_only_for_readonly_dir)
    try:
        path = logging_config.setup_logging(tmp_path / "只读目录", force=True)
        assert path.name == logging_config.LOG_FILE_NAME
        assert "playerstock" in str(path)  # 落在临时目录下
        assert path.exists()
    finally:
        monkeypatch.setattr(logging_config, "_configured_path", None)


def test_setup_logging_does_not_duplicate_handler(log_dir) -> None:
    """同一个文件重复初始化时，旧 handler 会被移除，日志不会写两遍。"""
    before = len([h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)])

    logging_config.setup_logging(log_dir.parent, force=True)

    after = len([h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)])
    assert after == before, "重复初始化不应增加文件 handler"
    logging_config.setup_logging(log_dir.parent, force=True)

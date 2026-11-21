"""运行日志落盘：出错时能自查，而不是只能盯控制台。

负责人：D（2026-11-07 新增；`app/core/` 属 B 的写入边界，本次为**纯新增文件**，
未改动任何既有逻辑，B 复核时可整文件删除而不影响其他功能）

**为什么需要它**：控制台的日志一关窗口就没了，线上（Render）的日志又只在网页里翻。
把日志同时写进 `logs/app.log`（按 2 MB 滚动、保留 3 份），排查时直接打开文件即可：

    Get-Content logs\\app.log -Tail 50            # 本地：最近 50 行
    GET /api/api/debug/logs?lines=100             # 线上：浏览器直接看（同一批日志）

**边界**：
- 只写"我们自己的"日志（root logger），uvicorn 的 access 日志仍走控制台；
- 日志里**从不出口令、token、连接串**——代码里没有任何一处把这三类写进 logger；
- 目录可用 `LOG_DIR` 覆盖；不可写时回退到系统临时目录，绝不让"日志失败"拖垮启动。
"""

from __future__ import annotations

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_NAME = "app.log"
MAX_BYTES = 2 * 1024 * 1024  # 单个文件 2 MB
BACKUP_COUNT = 3  # 保留 app.log.1 ~ app.log.3

_configured_path: Path | None = None


def default_log_dir() -> Path:
    """优先 `LOG_DIR`；否则用仓库根的 `logs/`（已进 .gitignore）。"""
    env_dir = os.getenv("LOG_DIR")
    if env_dir:
        return Path(env_dir)
    # <repo>/code/backend/app/core/logging_config.py → parents[4] == <repo>
    return Path(__file__).resolve().parents[4] / "logs"


def _open_handler(path: Path) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    return handler


def setup_logging(log_dir: str | Path | None = None, *, force: bool = False) -> Path:
    """把日志同时写到控制台与 `logs/app.log`，返回实际使用的文件路径。

    幂等：重复调用只生效一次（除非 `force=True`，供测试用）。
    """
    global _configured_path
    if _configured_path is not None and not force:
        return _configured_path

    target = (Path(log_dir) if log_dir else default_log_dir()) / LOG_FILE_NAME
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        handler = _open_handler(target)
    except OSError:  # 目录不可写（只读文件系统等）→ 退到临时目录，绝不阻断启动
        target = Path(tempfile.gettempdir()) / "playerstock" / LOG_FILE_NAME
        target.parent.mkdir(parents=True, exist_ok=True)
        handler = _open_handler(target)

    # 去重：同一个文件不要挂两个 handler（否则每行日志写两遍）
    for existing in list(root.handlers):
        if isinstance(existing, RotatingFileHandler) and Path(
            existing.baseFilename
        ).resolve() == target.resolve():
            root.removeHandler(existing)

    root.addHandler(handler)

    # 第三方库的 INFO 会把真实错误淹没（httpx 每发一个请求打一行），统一压到 WARNING
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured_path = target
    return target


def current_log_path() -> Path | None:
    """已配置的日志文件路径（未初始化时为 None）。"""
    return _configured_path


def recent_lines(count: int = 100, *, path: Path | None = None) -> list[str]:
    """读取日志文件最后 `count` 行；文件不存在时返回空列表。"""
    target = path or _configured_path or (default_log_dir() / LOG_FILE_NAME)
    if not target.exists():
        return []
    safe_count = max(1, min(int(count), 500))
    with target.open("r", encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()[-safe_count:]

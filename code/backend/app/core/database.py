"""数据库引擎与会话。

负责人：B

注意 SQLite 的三个坑：
1. 多线程访问需要 check_same_thread=False，否则 FastAPI 的线程池里会报错；
2. 外键默认是关闭的，不执行 PRAGMA foreign_keys=ON 等于没有外键约束；
3. 写写并发会报 "database is locked"，用 WAL + busy_timeout 缓解。

事务边界：余额/持仓/流水必须同事务提交，接口层失败时整体 rollback。
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    # 托管 Postgres 空闲后连接可能被服务端断开；免费实例还会休眠。
    # pool_pre_ping 会在取连接时先探活，避免第一个请求报 "server closed the connection"。
    pool_pre_ping=not settings.is_sqlite,
    future=True,
)

if settings.is_sqlite:

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


# expire_on_commit=False：提交后仍可读 trade.created_at 等字段拼响应，不再触发额外 SELECT
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表（开发期用；生产迁移属于加分项，6 天版不做 Alembic）。"""
    from app import models  # noqa: F401  确保模型已注册到 Base.metadata

    Base.metadata.create_all(bind=engine)

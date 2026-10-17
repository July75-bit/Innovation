"""数据库引擎与会话。

负责人：B

注意 SQLite 的两个坑：
1. 多线程访问需要 check_same_thread=False，否则 FastAPI 的线程池里会报错；
2. 事务边界由 API 层用 `with db.begin():` 显式控制，余额/持仓/流水必须同事务提交。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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

"""pytest 公共夹具。

在仓库根目录运行（pyproject.toml 已配置 pythonpath = ["code/backend", "code"]）：
    python -m pytest

每个用例使用独立的临时 SQLite 库，并覆盖 ``get_db`` 依赖：
- 不会读写仓库里的 playerstock.db；
- 用例之间互不影响，CI 上也能直接跑。
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "code" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# 必须在 import app 之前设置，避免配置在仓库根目录生成数据库文件
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{(REPO_ROOT / '.pytest-tmp' / 'bootstrap.db').as_posix()}",
)

from app.core.database import Base, get_db  # noqa: E402
from app.core.time import utcnow  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Player, PriceHistory, User  # noqa: E402

SEED_ZYWOO = 1
SEED_ROPZ = 2
SEED_SH1RO = 7
SEED_FLAMEZ = 8


# tmp_path 基目录：钉在仓库内，不用系统 Temp（原因见 pytest_configure 注释）
PYTEST_BASETMP = REPO_ROOT / ".pytest-tmp" / "run"


def pytest_configure(config: pytest.Config) -> None:
    """把 pytest 的临时目录基址改到仓库内的 .pytest-tmp/run。

    默认行为是 %TEMP%/pytest-of-<user>/，而那个位置在 Windows 上很容易被外部工具
    （沙箱化的运行器等）用错误的 ACL 抢先建出来；一旦 ACL 坏了，**目录属主本人连
    scandir 都会被拒绝**，于是所有用到 tmp_path 的用例都在 setup 阶段报
    PermissionError: [WinError 5]，跟被测代码毫无关系，换台机器还复现不出来。
    第 7 轮合并 origin/develop 时就撞上这个，205 条用例里成片 ERROR。

    放进仓库内的固定目录有三个好处：任何机器 / agent / CI 只看同一个位置；
    目录每次运行由 pytest 自己清空重建；也不再会在仓库根目录甩出 pytest-of-*/。
    显式传了 --basetemp 时尊重调用方的选择，不覆盖。
    """
    # pytest 只 mkdir(basetemp) 本身，不会建父目录；缓存目录也落在同一个父目录下
    PYTEST_BASETMP.parent.mkdir(parents=True, exist_ok=True)
    # 显式传了 --basetemp 时尊重调用方的选择
    if config.option.basetemp is None:
        config.option.basetemp = str(PYTEST_BASETMP)


@pytest.fixture(autouse=True)
def _no_live_season_round(monkeypatch) -> None:
    """默认把"今天是不是比赛日"关掉，交易闸门只认手动 status。

    为什么要 autouse：`ensure_tradable_now` 会按 UTC 比赛日现查赛程，而演示赛季是
    连续 28 天（2026-11-01 ~ 11-28）——CI 或本地只要落在这段日期里，Vitality / Spirit
    等队的选手就会被整队停牌，一堆和赛程无关的用例会莫名其妙变红。
    要测"本轮停牌"的用例自己把轮次 patch 回去（见 tests/unit/test_api_trades.py）。
    """
    from app.core import rules

    monkeypatch.setattr(rules, "current_round", lambda schedule, today=None: None)


@pytest.fixture()
def session_factory(tmp_path):
    """临时库 + 固定演示数据（4 名选手，覆盖涨/跌/横盘/暂停交易）。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    Base.metadata.create_all(engine)

    now = utcnow()
    with factory() as db:
        db.add(
            User(
                nickname="demo",
                balance=Decimal("5000.00"),
                initial_balance=Decimal("5000.00"),
            )
        )

        # ZywOo：120 → 126，评级 88，可交易
        db.add(
            Player(
                player_id=SEED_ZYWOO,
                name="ZywOo",
                display_name="ZywOo",
                team="Vitality",
                role="AWPer",
                current_price=Decimal("126.00"),
                prev_price=Decimal("120.00"),
                rating=88,
                status="trading",
            )
        )
        db.add_all(
            [
                PriceHistory(
                    player_id=SEED_ZYWOO,
                    price=Decimal("120.00"),
                    reason="初始价格",
                    ts=now - timedelta(hours=2),
                ),
                PriceHistory(
                    player_id=SEED_ZYWOO,
                    price=Decimal("126.00"),
                    reason="模拟比赛表现提升（测试数据）",
                    ts=now - timedelta(hours=1),
                ),
            ]
        )

        # ropz：横盘且没有价格历史（验证 points: [] 不 404）
        db.add(
            Player(
                player_id=SEED_ROPZ,
                name="ropz",
                display_name="ropz",
                team="FaZe Clan",
                role="Lurker",
                current_price=Decimal("105.00"),
                prev_price=Decimal("105.00"),
                rating=78,
                status="trading",
            )
        )

        # sh1ro：比赛中，暂停交易
        db.add(
            Player(
                player_id=SEED_SH1RO,
                name="sh1ro",
                display_name="sh1ro",
                team="Spirit",
                role="AWPer",
                current_price=Decimal("136.50"),
                prev_price=Decimal("130.00"),
                rating=85,
                status="suspended",
            )
        )

        # flameZ：下跌案例
        db.add(
            Player(
                player_id=SEED_FLAMEZ,
                name="flameZ",
                display_name="flameZ",
                team="Vitality",
                role="Rifler",
                current_price=Decimal("63.00"),
                prev_price=Decimal("70.00"),
                rating=66,
                status="trading",
            )
        )
        db.commit()

    yield factory
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    """FastAPI 测试客户端，数据库依赖替换为临时库。"""
    from fastapi.testclient import TestClient

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------- 智能体测试替身

@pytest.fixture()
def fake_llm():
    """统一的「假模型」夹具：给 analyze(chat=...) 注入，永不出网。

    用法：
        def test_x(fake_llm):
            advice = analyze(ctx, chat=fake_llm.returning({...}))
            # 或者用预设：fake_llm.buy() / fake_llm.hold() / fake_llm.raw("脏文本")

    设计要点（课件「依赖可替换」原则）：
    - 记录被调用次数（fake_llm.calls），可断言"不该调模型时一次都没调"；
    - 可以返回任意原始文本（含脏输出），用于验证清洗与降级；
    - 不含任何网络/密钥，CI 上永远离线。
    """

    class _FakeLLM:
        def __init__(self) -> None:
            self.calls: list[str] = []
            self._payload: str = ""

        # -- 构造返回值 --
        def returning(self, payload: dict) -> "_FakeLLM":
            import json as _json
            self._payload = _json.dumps(payload, ensure_ascii=False)
            return self

        def raw(self, text: str) -> "_FakeLLM":
            self._payload = text
            return self

        def buyer(self) -> "_FakeLLM":
            return self.returning(
                {"action": "BUY", "reason": "近 5 个价格点累计上涨 8.2%（本轮得分 85.0）", "risk_level": "LOW"}
            )

        def holder(self) -> "_FakeLLM":
            return self.returning(
                {"action": "HOLD", "reason": "价格横盘，累计变动 0.0%（本轮得分 50.0）", "risk_level": "MEDIUM"}
            )

        def __call__(self, prompt: str) -> str:
            self.calls.append(prompt)
            return self._payload or "{}"

    return _FakeLLM()
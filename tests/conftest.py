"""pytest 公共夹具。

在仓库根目录运行（pyproject.toml 已配置 pythonpath = ["backend"]）：
    python -m pytest
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """FastAPI 测试客户端。"""
    return TestClient(app)

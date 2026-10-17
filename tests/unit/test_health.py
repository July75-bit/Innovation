"""健康检查测试 —— 已可运行，用于验证 CI 与本地环境是否正常。

负责人：B
"""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "playerstock-backend"}


def test_root_returns_project_info(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "PlayerStock"
    assert "version" in body

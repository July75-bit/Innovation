"""私人账号之间的**数据隔离**（第 7 轮的核心验收项）。

负责人：A

前面 `test_api_auth.py` 只证明"接口形状对"，这一文件证明真正花钱的那件事：
**注册出来的每个账号有自己的一份余额 / 持仓 / 流水，公共演示账户不受影响。**

夹具数据（tests/conftest.py）：ZywOo 126.00、flameZ 63.00（可交易）、sh1ro 暂停交易、
每个新建账号初始 5000 虚拟币、单人单选手上限 50 股。
选 flameZ 做上限用例：50 股 = 3150 才买得起，ZywOo 50 股要 6300 会先撞上余额不足。
"""

from __future__ import annotations

from sqlalchemy import func

from app.core.config import settings

SEED_ZYWOO = 1
SEED_FLAMEZ = 8
GOOD_PASSWORD = "cs2go1234"


def make_account(client, username: str) -> dict:
    """注册一个私人账号，返回可直接塞进 headers 的字典。"""
    resp = client.post("/api/auth/register", json={"username": username, "password": GOOD_PASSWORD})
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def delete_account(client, password=GOOD_PASSWORD, headers=None):
    """DELETE 带请求体只能走 client.request()：starlette TestClient 的 .delete() 不收 json=。

    真实浏览器 fetch 没这个限制（前端就是这么发的），所以这是测试客户端的怪癖，不是接口设计问题。
    """
    return client.request(
        "DELETE",
        "/api/auth/account",
        json={"password": password},
        headers=headers or {},
    )


def test_两个账号的余额与持仓互不可见(client):
    a = make_account(client, "alice")
    b = make_account(client, "bob")

    buy = client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 5}, headers=a)
    assert buy.status_code == 200, buy.text

    # A：钱扣了、持仓有了、流水一条
    assert client.get("/api/account", headers=a).json()["balance"] == 5000.0 - 126.0 * 5
    positions_a = client.get("/api/positions", headers=a).json()
    assert [row["quantity"] for row in positions_a] == [5]
    assert len(client.get("/api/trades", headers=a).json()) == 1

    # B：完全干净——这才是"私人账号"的意义
    assert client.get("/api/account", headers=b).json()["balance"] == 5000.0
    assert client.get("/api/positions", headers=b).json() == []
    assert client.get("/api/trades", headers=b).json() == []

    # B 想卖 A 的持仓：卖不掉（不允许卖空）
    sell = client.post("/api/trades/sell", json={"player_id": SEED_ZYWOO, "quantity": 1}, headers=b)
    assert sell.status_code == 400
    assert sell.json()["code"] == "INSUFFICIENT_POSITION"


def test_未登录仍然是那个公共演示账户(client):
    a = make_account(client, "alice")
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 5}, headers=a)

    # 不带 Authorization 的访客共用 demo：A 的买卖不该出现在这里
    positions = client.get("/api/positions").json()
    assert positions == []
    assert client.get("/api/trades").json() == []
    assert client.get("/api/account").json()["balance"] == float(settings.initial_balance)


def test_五十股上限按人算而不是全局(client):
    a = make_account(client, "alice")
    b = make_account(client, "bob")

    first = client.post("/api/trades/buy", json={"player_id": SEED_FLAMEZ, "quantity": 50}, headers=a)
    assert first.status_code == 200, first.text

    # A 再买 1 股：超的是"单人单选手 50 股"
    over = client.post("/api/trades/buy", json={"player_id": SEED_FLAMEZ, "quantity": 1}, headers=a)
    assert over.status_code == 400
    assert over.json()["code"] == "POSITION_LIMIT_EXCEEDED"  # 既有错误码，第 7 轮不改契约

    # B 同样买 50 股：上限不是全局占用，否则第 7 轮就白做了
    second = client.post(
        "/api/trades/buy", json={"player_id": SEED_FLAMEZ, "quantity": 50}, headers=b
    )
    assert second.status_code == 200, second.text
    assert client.get("/api/positions", headers=b).json()[0]["quantity"] == 50


def test_同一账号两次登录看到同一份数据(client):
    first = make_account(client, "alice")
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 3}, headers=first)

    login = client.post("/api/auth/login", json={"username": "alice", "password": GOOD_PASSWORD})
    assert login.status_code == 200
    second = {"Authorization": f"Bearer {login.json()['token']}"}

    # 两个令牌指向同一个账户：持仓不是"每次登录重置"
    assert client.get("/api/positions", headers=second).json()[0]["quantity"] == 3
    assert (
        client.get("/api/account", headers=second).json()["user_id"]
        == client.get("/api/account", headers=first).json()["user_id"]
    )


def test_退出后公共账户仍然能正常买卖(client):
    a = make_account(client, "alice")
    token = a["Authorization"]
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 1}, headers=a)

    logout = client.post("/api/auth/logout", headers={"Authorization": token})
    assert logout.status_code == 200
    # 令牌撤销后拿它请求必须 401，而不是悄悄变成访客（那是最危险的假退出）
    assert client.get("/api/positions", headers={"Authorization": token}).status_code == 401

    # 访客（demo）路径不受私人账号退出影响——答辩现场没登录也能演示
    guest_buy = client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 2})
    assert guest_buy.status_code == 200, guest_buy.text
    assert client.get("/api/positions").json()[0]["quantity"] == 2

    # A 重新登录：持仓仍是自己那 1 股，没被访客那笔污染（数据在账号上，不在令牌上）
    again = client.post("/api/auth/login", json={"username": "alice", "password": GOOD_PASSWORD})
    assert again.status_code == 200
    fresh = {"Authorization": f"Bearer {again.json()['token']}"}
    assert client.get("/api/positions", headers=fresh).json()[0]["quantity"] == 1


def test_删账号只删自己的数据(client):
    a = make_account(client, "alice")
    b = make_account(client, "bob")
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 5}, headers=a)
    client.post("/api/trades/buy", json={"player_id": SEED_FLAMEZ, "quantity": 10}, headers=b)

    del_a = delete_account(client, headers=a)
    assert del_a.status_code == 200, del_a.text

    # B 完全不受影响：持仓、余额、流水都是自己的那一份
    positions_b = client.get("/api/positions", headers=b).json()
    assert [(row["name"], row["quantity"]) for row in positions_b] == [("flameZ", 10)]
    assert client.get("/api/account", headers=b).json()["balance"] == 5000.0 - 63.0 * 10
    assert len(client.get("/api/trades", headers=b).json()) == 1

    # 公共演示账户不属于任何个人，删私人账号不该碰到它
    # （/api/account 按契约 §4.5 没有 nickname 字段，身份要从 §4.13 的 /me 取）
    me = client.get("/api/auth/me").json()
    assert me["authenticated"] is False
    assert me["user"]["nickname"] == "demo"
    assert me["user"]["account_type"] == "public_demo"


def test_删账号后公共路径照常且名字不再占用(client, session_factory):
    from sqlalchemy import select

    from app.models import AuthToken, Position, Trade, User

    a = make_account(client, "alice")
    token = a["Authorization"]
    client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 1}, headers=a)

    assert (
        delete_account(client, headers=a).status_code
        == 200
    )

    # 令牌随账号一起作废：拿旧令牌再请求必须 401，而不是悄悄退回公共账户
    assert client.get("/api/account", headers={"Authorization": token}).status_code == 401

    # 访客（demo）路径照常可用
    assert client.post("/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 1}).status_code == 200

    # 库里必须清干净：账号行、持仓行、流水行、令牌行都不再有 alice 的痕迹
    with session_factory() as db:
        assert db.scalar(select(User).where(User.nickname == "alice")) is None
        assert db.scalar(select(func.count()).select_from(Position)) == 1  # 只剩 demo 那一行
        assert db.scalar(select(func.count()).select_from(Trade)) == 1
        # 访客那笔买调用的是公共账户，公共账户不签发令牌（只有注册/登录才发），所以应为 0
        assert db.scalar(select(func.count()).select_from(AuthToken)) == 0
        names = sorted(row.nickname for row in db.scalars(select(User)).all())
    assert names == ["demo"]

    # 名字释放了，可以重新注册成全新账号
    again = client.post("/api/auth/register", json={"username": "alice", "password": GOOD_PASSWORD})
    assert again.status_code == 201
    assert again.json()["user"]["balance"] == 5000.0

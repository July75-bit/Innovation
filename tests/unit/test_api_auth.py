"""注册 / 登录 / 退出 / 当前身份接口的**返回内容契约**测试。

负责人：A（第 7 轮私人账号）

分工（沿用 test_api_trades.py 的三层拆法）：
- 本文件守"字段集合、状态码、错误码"——前端 useAuth 直接按这些分支写 UI；
- `tests/integration/test_auth_multiuser.py` 守"多账户数据隔离"（真金白银的余额/持仓）；
- `test_trades_rule.py` 那套交易规则不受本次改动影响，回归由它兜。

对应本轮最容易翻车的三条：
1. 注册成功后前端要立刻拿到 token 才能免二次登录；
2. 口令错误与账号不存在必须是同一句话（否则接口可以用来枚举账号名）；
3. 退出后旧 token 要**真的**失效，不是只删浏览器存储。
"""

from __future__ import annotations

# 与 tests/conftest.py 一致：公共演示账户的昵称
DEMO = "demo"

AUTH_KEYS = {"token", "expires_at", "user"}
USER_KEYS = {
    "user_id",
    "nickname",
    "balance",
    "initial_balance",
    "created_at",
    "account_type",
}
ERROR_KEYS = {"success", "message", "code"}

GOOD_PASSWORD = "cs2go1234"


def register(client, username="lan_player", password=GOOD_PASSWORD):
    return client.post("/api/auth/register", json={"username": username, "password": password})



def test_注册成功即登录(client):
    resp = register(client)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert set(body) == AUTH_KEYS
    assert set(body["user"]) == USER_KEYS
    assert body["token"]
    assert body["expires_at"].endswith("Z")
    assert body["user"]["nickname"] == "lan_player"
    assert body["user"]["balance"] == 5000.0
    assert body["user"]["account_type"] == "private"


def test_注册后_me_认出私人账户(client):
    token = register(client).json()["token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    body = me.json()
    assert body["authenticated"] is True
    assert body["user"]["account_type"] == "private"


def test_不带令牌时_me_报公共演示账户(client):
    body = client.get("/api/auth/me").json()

    assert body["authenticated"] is False
    assert body["user"]["nickname"] == DEMO
    assert body["user"]["account_type"] == "public_demo"


def test_用户名重复直接拒绝且大小写同规则(client):
    first = register(client, username="ZywOoFan")
    assert first.status_code == 201

    dup = register(client, username="zywoofan")

    assert dup.status_code == 409
    assert set(dup.json()) == ERROR_KEYS
    assert dup.json()["code"] == "USERNAME_TAKEN"


def test_demo_是保留名不能被注册(client):
    resp = register(client, username=DEMO)

    assert resp.status_code == 409
    assert resp.json()["code"] == "USERNAME_RESERVED"


def test_非法用户名与弱密码都是_422(client):
    bad_name = register(client, username="a b")
    weak_pwd = register(client, username="okname", password="abcdefgh")
    short_pwd = register(client, username="okname", password="ab1")

    assert bad_name.status_code == 422
    assert bad_name.json()["code"] == "INVALID_INPUT"
    assert weak_pwd.status_code == 422
    assert "字母和数字" in weak_pwd.json()["message"]
    assert short_pwd.json()["code"] == "INVALID_INPUT"


def test_口令错误与账号不存在同一句话(client):
    register(client, username="lan_player")

    wrong_pwd = client.post(
        "/api/auth/login", json={"username": "lan_player", "password": "wrongpass1"}
    )
    no_such = client.post(
        "/api/auth/login", json={"username": "nobody_here", "password": GOOD_PASSWORD}
    )

    assert wrong_pwd.status_code == 401
    assert no_such.status_code == 401
    # 两条提示一致：不能靠 message 区分出"这个账号名存在"
    assert wrong_pwd.json()["message"] == no_such.json()["message"]
    assert wrong_pwd.json()["code"] == "INVALID_CREDENTIALS"


def test_登录成功换到新令牌(client):
    register(client, username="lan_player")

    login = client.post(
        "/api/auth/login", json={"username": "Lan_Player", "password": GOOD_PASSWORD}
    )

    assert login.status_code == 200
    assert set(login.json()) == AUTH_KEYS
    assert login.json()["user"]["nickname"] == "lan_player"


def test_公共演示账户不能用密码登录(client):
    resp = client.post("/api/auth/login", json={"username": DEMO, "password": GOOD_PASSWORD})

    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


def test_退出后旧令牌真的失效(client):
    token = register(client).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["revoked"] is True

    after = client.get("/api/auth/me", headers=headers)
    assert after.status_code == 401
    assert after.json()["code"] == "UNAUTHORIZED"


def test_没带令牌调用退出也是幂等成功(client):
    resp = client.post("/api/auth/logout")

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["revoked"] is False


def test_乱码令牌_401_而不是当成访客(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_认证头格式不对给明确提示(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Token abc123"})

    assert resp.status_code == 401
    assert "Bearer" in resp.json()["message"]


def test_过期令牌被拒(client, session_factory):
    from datetime import timedelta

    from sqlalchemy import select

    from app.core.security import hash_token
    from app.core.time import utcnow
    from app.models import AuthToken, User

    token = register(client, username="lan_player").json()["token"]

    # 直接把库里的过期时间拨到过去：比伪造一个"看起来过期"的字符串更贴近真实故障
    with session_factory() as db:
        row = db.get(AuthToken, hash_token(token))
        assert row is not None
        row.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 401
    with session_factory() as db:
        assert db.scalar(select(User).where(User.nickname == "lan_player")) is not None


def test_库里不存明文口令(client, session_factory):
    from sqlalchemy import select

    from app.models import User

    register(client, username="lan_player", password=GOOD_PASSWORD)

    with session_factory() as db:
        user = db.scalar(select(User).where(User.nickname == "lan_player"))
        assert user is not None
        assert GOOD_PASSWORD not in (user.password_hash or "")
        assert user.password_hash.startswith("pbkdf2_sha256$")
        assert user.salt and len(user.salt) == 32
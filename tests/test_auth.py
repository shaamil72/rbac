from tests.conftest import make_user


def test_login_success(client, db):
    make_user(db, "alice", password="secret99")
    r = client.post("/auth/token", data={"username": "alice", "password": "secret99"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_bad_password(client, db):
    make_user(db, "alice", password="correct")
    r = client.post("/auth/token", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/token", data={"username": "ghost", "password": "anything"})
    assert r.status_code == 401


def test_login_inactive_user(client, db):
    make_user(db, "frozen", password="pass1234", is_active=False)
    r = client.post("/auth/token", data={"username": "frozen", "password": "pass1234"})
    assert r.status_code == 403


def test_no_token_returns_401(client):
    assert client.get("/users").status_code == 401

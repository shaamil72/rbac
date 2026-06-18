from tests.conftest import make_user, make_role, auth_headers


# ── permission enforcement ──────────────────────────────────────────────────

def test_list_users_no_token(client):
    assert client.get("/users").status_code == 401


def test_list_users_no_permission(client, noperm_h):
    assert client.get("/users", headers=noperm_h).status_code == 403


def test_list_users_ok(client, admin_h):
    assert client.get("/users", headers=admin_h).status_code == 200


def test_create_user_requires_write_users(client, readonly_h):
    r = client.post("/users",
                    json={"username": "new", "email": "new@x.com", "password": "abc123"},
                    headers=readonly_h)
    assert r.status_code == 403


def test_delete_user_requires_delete_perm(client, db, admin_h, perms):
    # write:users is not enough — delete:users is required
    role = make_role(db, "Writer", [perms["write:users"], perms["read:users"]])
    writer = make_user(db, "writer", roles=[role])
    w_h = auth_headers(writer)

    r = client.post("/users",
                    json={"username": "target", "email": "t@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]

    assert client.delete(f"/users/{uid}", headers=w_h).status_code == 403
    assert client.delete(f"/users/{uid}", headers=admin_h).status_code == 204


# ── CRUD ────────────────────────────────────────────────────────────────────

def test_create_and_get_user(client, admin_h):
    r = client.post("/users",
                    json={"username": "bob", "email": "bob@x.com", "password": "abc123"},
                    headers=admin_h)
    assert r.status_code == 201
    uid = r.json()["id"]

    r2 = client.get(f"/users/{uid}", headers=admin_h)
    assert r2.status_code == 200
    assert r2.json()["username"] == "bob"


def test_create_user_conflict(client, admin_h):
    payload = {"username": "dup", "email": "dup@x.com", "password": "abc123"}
    client.post("/users", json=payload, headers=admin_h)
    assert client.post("/users", json=payload, headers=admin_h).status_code == 409


def test_get_nonexistent_user(client, admin_h):
    assert client.get("/users/9999", headers=admin_h).status_code == 404


def test_update_user(client, admin_h):
    r = client.post("/users",
                    json={"username": "carol", "email": "carol@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]
    r2 = client.patch(f"/users/{uid}", json={"is_active": False}, headers=admin_h)
    assert r2.status_code == 200
    assert r2.json()["is_active"] is False


def test_delete_user(client, admin_h):
    r = client.post("/users",
                    json={"username": "dave", "email": "dave@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]
    assert client.delete(f"/users/{uid}", headers=admin_h).status_code == 204
    assert client.get(f"/users/{uid}", headers=admin_h).status_code == 404


def test_change_password(client, admin_h):
    r = client.post("/users",
                    json={"username": "eve", "email": "eve@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]
    assert client.patch(f"/users/{uid}/password",
                        json={"new_password": "newpass99"},
                        headers=admin_h).status_code == 200


def test_change_password_too_short(client, admin_h):
    r = client.post("/users",
                    json={"username": "frank", "email": "frank@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]
    assert client.patch(f"/users/{uid}/password",
                        json={"new_password": "12345"},
                        headers=admin_h).status_code == 422


def test_assign_and_remove_role(client, admin_h):
    r = client.post("/users",
                    json={"username": "grace", "email": "g@x.com", "password": "abc123"},
                    headers=admin_h)
    uid = r.json()["id"]

    rr = client.post("/roles", json={"name": "Tester"}, headers=admin_h)
    rid = rr.json()["id"]

    assert client.post(f"/users/{uid}/roles/{rid}", headers=admin_h).status_code == 200
    u = client.get(f"/users/{uid}", headers=admin_h).json()
    assert any(role["id"] == rid for role in u["roles"])

    assert client.delete(f"/users/{uid}/roles/{rid}", headers=admin_h).status_code == 200
    u2 = client.get(f"/users/{uid}", headers=admin_h).json()
    assert not any(role["id"] == rid for role in u2["roles"])


def test_get_user_permissions(client, readonly, readonly_h):
    r = client.get(f"/users/{readonly.id}/permissions", headers=readonly_h)
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["permissions"]]
    assert "read:users" in names

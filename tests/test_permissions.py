from tests.conftest import make_role, make_user, auth_headers


def test_list_permissions_no_permission(client, noperm_h):
    assert client.get("/permissions", headers=noperm_h).status_code == 403


def test_list_permissions_ok(client, admin_h):
    assert client.get("/permissions", headers=admin_h).status_code == 200


def test_create_permission(client, admin_h):
    r = client.post("/permissions",
                    json={"name": "read:reports", "resource": "reports"},
                    headers=admin_h)
    assert r.status_code == 201
    assert r.json()["name"] == "read:reports"


def test_create_permission_conflict(client, admin_h):
    payload = {"name": "dup:thing", "resource": "thing"}
    client.post("/permissions", json=payload, headers=admin_h)
    assert client.post("/permissions", json=payload, headers=admin_h).status_code == 409


def test_create_permission_requires_write_permissions(client, db, perms):
    role = make_role(db, "PermReader", [perms["read:permissions"]])
    user = make_user(db, "permreader", roles=[role])
    headers = auth_headers(user)
    assert client.post("/permissions",
                       json={"name": "x:y", "resource": "y"},
                       headers=headers).status_code == 403


def test_get_permission(client, admin_h):
    r = client.post("/permissions",
                    json={"name": "write:reports", "resource": "reports"},
                    headers=admin_h)
    pid = r.json()["id"]
    r2 = client.get(f"/permissions/{pid}", headers=admin_h)
    assert r2.status_code == 200
    assert r2.json()["name"] == "write:reports"


def test_get_nonexistent_permission(client, admin_h):
    assert client.get("/permissions/9999", headers=admin_h).status_code == 404


def test_delete_permission(client, admin_h):
    r = client.post("/permissions",
                    json={"name": "temp:thing", "resource": "thing"},
                    headers=admin_h)
    pid = r.json()["id"]
    assert client.delete(f"/permissions/{pid}", headers=admin_h).status_code == 204

from tests.conftest import make_role, make_user, auth_headers


def test_list_roles_no_permission(client, noperm_h):
    assert client.get("/roles", headers=noperm_h).status_code == 403


def test_list_roles_ok(client, admin_h):
    assert client.get("/roles", headers=admin_h).status_code == 200


def test_create_role(client, admin_h):
    r = client.post("/roles", json={"name": "Auditor", "description": "Read-only auditor"},
                    headers=admin_h)
    assert r.status_code == 201
    assert r.json()["name"] == "Auditor"


def test_create_role_conflict(client, admin_h):
    client.post("/roles", json={"name": "Dup"}, headers=admin_h)
    assert client.post("/roles", json={"name": "Dup"}, headers=admin_h).status_code == 409


def test_create_role_requires_write_roles(client, db, perms):
    role = make_role(db, "RoleReader", [perms["read:roles"]])
    user = make_user(db, "rolereader", roles=[role])
    headers = auth_headers(user)
    assert client.post("/roles", json={"name": "X"}, headers=headers).status_code == 403


def test_get_role(client, admin_h):
    r = client.post("/roles", json={"name": "Viewer"}, headers=admin_h)
    rid = r.json()["id"]
    r2 = client.get(f"/roles/{rid}", headers=admin_h)
    assert r2.status_code == 200
    assert r2.json()["name"] == "Viewer"


def test_get_nonexistent_role(client, admin_h):
    assert client.get("/roles/9999", headers=admin_h).status_code == 404


def test_delete_role(client, admin_h):
    r = client.post("/roles", json={"name": "ToDelete"}, headers=admin_h)
    rid = r.json()["id"]
    assert client.delete(f"/roles/{rid}", headers=admin_h).status_code == 204


def test_assign_and_remove_permission(client, admin_h, perms):
    r = client.post("/roles", json={"name": "Custom"}, headers=admin_h)
    rid = r.json()["id"]
    pid = perms["read:logs"].id

    assert client.post(f"/roles/{rid}/permissions/{pid}", headers=admin_h).status_code == 200
    role = client.get(f"/roles/{rid}", headers=admin_h).json()
    assert any(p["id"] == pid for p in role["permissions"])

    assert client.delete(f"/roles/{rid}/permissions/{pid}", headers=admin_h).status_code == 200
    role2 = client.get(f"/roles/{rid}", headers=admin_h).json()
    assert not any(p["id"] == pid for p in role2["permissions"])

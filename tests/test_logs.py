def test_list_logs_no_permission(client, noperm_h):
    assert client.get("/logs", headers=noperm_h).status_code == 403


def test_list_logs_ok(client, admin_h):
    r = client.get("/logs", headers=admin_h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_logs_entries_created(client, admin_h):
    client.post("/users",
                json={"username": "logged", "email": "l@x.com", "password": "abc123"},
                headers=admin_h)
    r = client.get("/logs", headers=admin_h)
    assert any("create_user" in entry["action"] for entry in r.json())


def test_list_logs_filter_by_user(client, admin, admin_h):
    r = client.get(f"/logs?user_id={admin.id}", headers=admin_h)
    assert r.status_code == 200
    for entry in r.json():
        assert entry["user_id"] == admin.id

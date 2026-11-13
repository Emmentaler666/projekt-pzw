def test_list_requires_login(client):
    r = client.get("/equipment")
    assert r.status_code == 401
    assert r.json()["code"] == "not_authenticated"


def test_student_can_list_with_pagination(client, student1_h):
    r = client.get("/equipment", params={"limit": 2, "offset": 1}, headers=student1_h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert [e["id"] for e in body["items"]] == [2, 3]


def test_invalid_limit_is_422(client, student1_h):
    r = client.get("/equipment", params={"limit": 0}, headers=student1_h)
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"


def test_student_cannot_create_equipment(client, student1_h):
    data = {"name": "Mikrofon", "inventory_number": "T-100"}
    r = client.post("/equipment", json=data, headers=student1_h)
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


def test_admin_can_create_equipment(client, admin_h):
    data = {"name": "Mikrofon", "inventory_number": "T-100"}
    r = client.post("/equipment", json=data, headers=admin_h)
    assert r.status_code == 201
    assert r.json()["inventory_number"] == "T-100"


def test_duplicate_inventory_number_is_409(client, admin_h):
    data = {"name": "Drugi laptop", "inventory_number": "T-001"}
    r = client.post("/equipment", json=data, headers=admin_h)
    assert r.status_code == 409
    assert r.json()["code"] == "inventory_number_taken"


def test_patch_changes_only_given_fields(client, admin_h):
    r = client.patch("/equipment/1", json={"name": "Novo ime"}, headers=admin_h)
    assert r.status_code == 200
    assert r.json()["name"] == "Novo ime"
    assert r.json()["inventory_number"] == "T-001"


def test_student_cannot_patch_or_delete(client, student1_h):
    patch = client.patch("/equipment/1", json={"name": "X"}, headers=student1_h)
    delete = client.delete("/equipment/1", headers=student1_h)
    assert patch.status_code == 403
    assert delete.status_code == 403


def test_missing_equipment_is_404(client, student1_h):
    r = client.get("/equipment/9999", headers=student1_h)
    assert r.status_code == 404
    assert r.json()["code"] == "equipment_not_found"


def test_cannot_delete_equipment_with_loans(client, student1_h, admin_h):
    client.post("/loans", json={"equipment_id": 1}, headers=student1_h)
    r = client.delete("/equipment/1", headers=admin_h)
    assert r.status_code == 409
    assert r.json()["code"] == "equipment_has_loans"


def test_admin_can_delete_free_equipment(client, admin_h):
    r = client.delete("/equipment/4", headers=admin_h)
    assert r.status_code == 204
    assert client.get("/equipment/4", headers=admin_h).status_code == 404
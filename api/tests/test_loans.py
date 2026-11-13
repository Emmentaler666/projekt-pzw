from datetime import datetime, timezone

from freezegun import freeze_time

from tests.helpers import auth_headers


def borrow(client, headers, equipment_id):
    return client.post("/loans", json={"equipment_id": equipment_id}, headers=headers)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_loans_require_login(client):
    r = client.get("/loans")
    assert r.status_code == 401


def test_create_loan_sets_14_day_deadline(client):
    with freeze_time("2026-03-01 10:00:00"):
        headers = auth_headers(client, "student1")
        r = borrow(client, headers, 1)
    assert r.status_code == 201
    body = r.json()
    assert datetime.fromisoformat(body["borrowed_at"]) == utc(2026, 3, 1, 10, 0)
    assert datetime.fromisoformat(body["due_at"]) == utc(2026, 3, 15, 10, 0)
    assert body["returned_at"] is None
    assert body["extended"] is False


def test_borrow_missing_equipment_is_404(client, student1_h):
    r = borrow(client, student1_h, 9999)
    assert r.status_code == 404
    assert r.json()["code"] == "equipment_not_found"


def test_student_cannot_exceed_three_active_loans(client, student1_h):
    for equipment_id in (1, 2, 3):
        assert borrow(client, student1_h, equipment_id).status_code == 201
    r = borrow(client, student1_h, 4)
    assert r.status_code == 409
    assert r.json()["code"] == "loan_limit_reached"


def test_returning_frees_a_slot(client, student1_h):
    first = borrow(client, student1_h, 1).json()
    borrow(client, student1_h, 2)
    borrow(client, student1_h, 3)
    client.post(f"/loans/{first['id']}/return", headers=student1_h)
    assert borrow(client, student1_h, 4).status_code == 201


def test_equipment_cannot_be_borrowed_twice(client, student1_h, student2_h):
    assert borrow(client, student1_h, 1).status_code == 201
    r = borrow(client, student2_h, 1)
    assert r.status_code == 409
    assert r.json()["code"] == "equipment_unavailable"


def test_returned_equipment_can_be_borrowed_again(client, student1_h, student2_h):
    loan = borrow(client, student1_h, 1).json()
    client.post(f"/loans/{loan['id']}/return", headers=student1_h)
    assert borrow(client, student2_h, 1).status_code == 201


def test_student_sees_only_own_loans(client, student1_h, student2_h):
    borrow(client, student1_h, 1)
    borrow(client, student2_h, 2)
    body = client.get("/loans", headers=student1_h).json()
    assert body["total"] == 1
    assert body["items"][0]["equipment_id"] == 1


def test_admin_sees_all_loans(client, student1_h, student2_h, admin_h):
    borrow(client, student1_h, 1)
    borrow(client, student2_h, 2)
    body = client.get("/loans", headers=admin_h).json()
    assert body["total"] == 2


def test_student_cannot_read_other_students_loan(client, student1_h, student2_h):
    loan = borrow(client, student1_h, 1).json()
    r = client.get(f"/loans/{loan['id']}", headers=student2_h)
    assert r.status_code == 404
    assert r.json()["code"] == "loan_not_found"


def test_student_cannot_return_or_extend_others_loan(client, student1_h, student2_h):
    loan = borrow(client, student1_h, 1).json()
    returned = client.post(f"/loans/{loan['id']}/return", headers=student2_h)
    extended = client.post(f"/loans/{loan['id']}/extend", headers=student2_h)
    assert returned.status_code == 404
    assert extended.status_code == 404
    untouched = client.get(f"/loans/{loan['id']}", headers=student1_h).json()
    assert untouched["returned_at"] is None
    assert untouched["extended"] is False


def test_admin_can_read_any_loan(client, student1_h, admin_h):
    loan = borrow(client, student1_h, 1).json()
    r = client.get(f"/loans/{loan['id']}", headers=admin_h)
    assert r.status_code == 200


def test_extend_adds_7_days_once(client):
    with freeze_time("2026-03-01 10:00:00"):
        headers = auth_headers(client, "student1")
        loan = borrow(client, headers, 1).json()
        first = client.post(f"/loans/{loan['id']}/extend", headers=headers)
        second = client.post(f"/loans/{loan['id']}/extend", headers=headers)
    assert first.status_code == 200
    assert datetime.fromisoformat(first.json()["due_at"]) == utc(2026, 3, 22, 10, 0)
    assert first.json()["extended"] is True
    assert second.status_code == 409
    assert second.json()["code"] == "already_extended"


def test_cannot_extend_after_deadline(client):
    with freeze_time("2026-03-01 10:00:00"):
        headers = auth_headers(client, "student1")
        loan = borrow(client, headers, 1).json()
    with freeze_time("2026-03-15 10:01:00"):
        headers = auth_headers(client, "student1")
        r = client.post(f"/loans/{loan['id']}/extend", headers=headers)
    assert r.status_code == 409
    assert r.json()["code"] == "loan_overdue"


def test_can_extend_just_before_deadline(client):
    with freeze_time("2026-03-01 10:00:00"):
        headers = auth_headers(client, "student1")
        loan = borrow(client, headers, 1).json()
    with freeze_time("2026-03-15 09:59:00"):
        headers = auth_headers(client, "student1")
        r = client.post(f"/loans/{loan['id']}/extend", headers=headers)
    assert r.status_code == 200


def test_returned_loan_cannot_be_returned_or_extended(client, student1_h):
    loan = borrow(client, student1_h, 1).json()
    assert client.post(f"/loans/{loan['id']}/return", headers=student1_h).status_code == 200
    again = client.post(f"/loans/{loan['id']}/return", headers=student1_h)
    extend = client.post(f"/loans/{loan['id']}/extend", headers=student1_h)
    assert again.status_code == 409
    assert again.json()["code"] == "already_returned"
    assert extend.status_code == 409
    assert extend.json()["code"] == "already_returned"


def test_active_filter(client, student1_h):
    first = borrow(client, student1_h, 1).json()
    borrow(client, student1_h, 2)
    client.post(f"/loans/{first['id']}/return", headers=student1_h)
    active = client.get("/loans", params={"active": "true"}, headers=student1_h).json()
    finished = client.get("/loans", params={"active": "false"}, headers=student1_h).json()
    assert active["total"] == 1
    assert finished["total"] == 1


def test_loans_pagination(client, student1_h):
    borrow(client, student1_h, 1)
    borrow(client, student1_h, 2)
    body = client.get("/loans", params={"limit": 1}, headers=student1_h).json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
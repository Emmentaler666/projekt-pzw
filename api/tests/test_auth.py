from freezegun import freeze_time

from tests.helpers import PASSWORD, auth_headers, login


def test_login_returns_token_pair(client):
    r = login(client, "student1")
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_wrong_password_and_unknown_user_give_same_response(client):
    wrong_password = login(client, "student1", "kriva-lozinka")
    unknown_user = login(client, "nepostojeci", PASSWORD)
    assert wrong_password.status_code == 401
    assert wrong_password.status_code == unknown_user.status_code
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["code"] == "invalid_credentials"


def test_me_without_token_is_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["code"] == "not_authenticated"


def test_me_returns_user_without_password_hash(client):
    r = client.get("/auth/me", headers=auth_headers(client, "student1"))
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "student1"
    assert body["role"] == "student"
    assert "password_hash" not in body


def test_refresh_returns_new_token_pair(client):
    tokens = login(client, "student1").json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_access_token_cannot_be_used_as_refresh_token(client):
    tokens = login(client, "student1").json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401
    assert r.json()["code"] == "invalid_token"


def test_refresh_token_cannot_be_used_as_access_token(client):
    tokens = login(client, "student1").json()
    headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 401


def test_expired_access_token_is_rejected(client):
    with freeze_time("2026-03-01 10:00:00"):
        headers = auth_headers(client, "student1")
    with freeze_time("2026-03-01 10:16:00"):
        r = client.get("/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["code"] == "invalid_token"
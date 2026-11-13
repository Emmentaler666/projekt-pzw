PASSWORD = "test123"


def login(client, username, password=PASSWORD):
    return client.post("/auth/login", json={"username": username, "password": password})


def auth_headers(client, username):
    token = login(client, username).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
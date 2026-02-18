def test_register_returns_token_and_user(client, unique_email):
    email = unique_email("register")
    response = client.post(
        "/auth/register",
        json={"name": "Auth User", "email": email, "password": "password123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert "id" in data["user"]


def test_register_duplicate_email_returns_409(client, unique_email):
    email = unique_email("dup")
    payload = {"name": "User A", "email": email, "password": "password123"}
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


def test_login_success_returns_token(client, unique_email):
    email = unique_email("login")
    client.post(
        "/auth/register", json={"name": "Login User", "email": email, "password": "password123"}
    )
    response = client.post("/auth/login", json={"email": email, "password": "password123"})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email


def test_login_invalid_password_returns_401(client, unique_email):
    email = unique_email("wrongpass")
    client.post(
        "/auth/register", json={"name": "Wrong Pass", "email": email, "password": "password123"}
    )
    response = client.post("/auth/login", json={"email": email, "password": "incorrect"})

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 403


def test_me_returns_current_user(client, auth_user):
    response = client.get("/auth/me", headers=auth_user["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == auth_user["user"]["id"]
    assert data["email"] == auth_user["user"]["email"]

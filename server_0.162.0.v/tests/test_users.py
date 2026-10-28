def test_create_user_success(client):
    res = client.post("/users", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "StrongPass1!",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice"
    assert "user_id" in data
    assert "password" not in data


def test_create_user_weak_password(client):
    res = client.post("/users", json={
        "name": "Bob",
        "email": "bob@example.com",
        "password": "weakpassword123",
    })
    assert res.status_code == 422


def test_create_user_invalid_email(client):
    res = client.post("/users", json={
        "name": "Bob",
        "email": "not-an-email",
        "password": "StrongPass1!",
    })
    assert res.status_code == 422


def test_get_user_by_id(client, test_user):
    res = client.get(f"/users/{test_user['user_id']}")
    assert res.status_code == 200
    assert res.json()["email"] == test_user["email"]


def test_get_user_not_found(client):
    res = client.get("/users/9999")
    assert res.status_code == 404
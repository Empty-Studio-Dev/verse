def test_login_success(client, test_user):
    res = client.post("/login", data={
        "username": test_user["email"],
        "password": test_user["password"],
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    res = client.post("/login", data={
        "username": test_user["email"],
        "password": "WrongPass1!",
    })
    assert res.status_code == 401


def test_login_user_not_found(client):
    res = client.post("/login", data={
        "username": "ghost@example.com",
        "password": "SomePass1!",
    })
    assert res.status_code == 404
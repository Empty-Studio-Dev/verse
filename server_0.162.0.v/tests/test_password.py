import pytest
from models import PasswordResetToken


@pytest.fixture(autouse=True)
def mock_email(monkeypatch):
    sent = {}

    def fake_send(to_email, token):
        sent["to"] = to_email
        sent["token"] = token 

    monkeypatch.setattr("routers.password_router.send_password_reset_email", fake_send)
    return sent


def test_forgot_password_existing_user(client, test_user, mock_email):
    res = client.post("/users/forgot-password", json={"email": test_user["email"]})
    assert res.status_code == 202
    assert mock_email["to"] == test_user["email"]
    assert "token" in mock_email


def test_forgot_password_unknown_email(client, mock_email):
    res = client.post("/users/forgot-password", json={"email": "nobody@example.com"})
    assert res.status_code == 202
    assert "to" not in mock_email


def test_reset_password_full_flow(client, test_user, mock_email):
    client.post("/users/forgot-password", json={"email": test_user["email"]})
    token = mock_email["token"]

    res = client.post("/users/reset-password", json={
        "token": token,
        "new_password": "BrandNewPass9!",
    })
    assert res.status_code == 200

    res = client.post("/login", data={
        "username": test_user["email"],
        "password": "BrandNewPass9!",
    })
    assert res.status_code == 200


def test_reset_password_invalid_token(client):
    res = client.post("/users/reset-password", json={
        "token": "totally-fake-token",
        "new_password": "BrandNewPass9!",
    })
    assert res.status_code == 400


def test_reset_password_weak_password(client, test_user, mock_email):
    client.post("/users/forgot-password", json={"email": test_user["email"]})
    token = mock_email["token"]

    res = client.post("/users/reset-password", json={
        "token": token,
        "new_password": "weak",
    })
    assert res.status_code == 422
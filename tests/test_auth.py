from datetime import datetime, timedelta, timezone

import jwt

from app.auth import secret_key


def test_frontend_and_api_health_are_served(client):
    frontend = client.get("/")
    health = client.get("/health")

    assert frontend.status_code == 200
    assert "<!doctype html>" in frontend.text.lower()
    assert health.status_code == 200
    assert health.json()["message"] == "Support Ticket API is running"


def test_login_issues_expiring_access_token(client):
    registration = client.post(
        "/users/register",
        json={
            "name": "Test Customer",
            "email": "customer@example.com",
            "password": "correct-horse-battery",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/users/login",
        json={
            "email": "customer@example.com",
            "password": "correct-horse-battery",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    claims = jwt.decode(token, secret_key, algorithms=["HS256"])
    assert claims["exp"] > datetime.now(timezone.utc).timestamp()

    profile = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "customer@example.com"


def test_expired_or_non_expiring_tokens_are_rejected(client):
    expired_token = jwt.encode(
        {
            "user_id": 1,
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        secret_key,
        algorithm="HS256",
    )
    legacy_token = jwt.encode(
        {"user_id": 1, "role": "user"},
        secret_key,
        algorithm="HS256",
    )

    for token in (expired_token, legacy_token):
        response = client.get(
            "/user/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

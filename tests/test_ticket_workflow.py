from app.ai.service import AIServiceError
from app.routes import ticket as ticket_routes
from tests.conftest import create_user


def test_ai_failure_escalates_and_ticket_access_is_scoped(client, db, monkeypatch):
    owner = create_user(db, "Owner", "owner@example.com", "user")
    agent = create_user(db, "Agent", "agent@example.com", "support_agent")
    outsider = create_user(db, "Outsider", "outsider@example.com", "user")

    def unavailable(*args, **kwargs):
        raise AIServiceError("provider is unavailable")

    monkeypatch.setattr(ticket_routes, "triage_ticket", unavailable)

    owner_token = client.post(
        "/users/login",
        json={"email": "owner@example.com", "password": "correct-horse-battery"},
    ).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    created = client.post(
        "/ticket",
        json={"title": "Cannot access account", "desc": "Please help me sign in."},
        headers=owner_headers,
    )

    assert created.status_code == 201
    ticket_data = created.json()
    assert ticket_data["ai_outcome"] == "escalated"
    assert ticket_data["assigned_to"] == agent.id

    outsider_token = client.post(
        "/users/login",
        json={"email": "outsider@example.com", "password": "correct-horse-battery"},
    ).json()["access_token"]
    denied = client.get(
        f"/ticket/{ticket_data['id']}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert denied.status_code == 403

    owner_result = client.get(
        f"/ticket/{ticket_data['id']}",
        headers=owner_headers,
    )
    assert owner_result.status_code == 200
    assert owner_result.json()["user_id"] == owner.id

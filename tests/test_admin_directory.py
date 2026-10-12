from tests.conftest import create_user


def test_user_directory_requires_admin(client, db):
    customer = create_user(db, "Customer", "customer@example.com", "user")
    token = client.post(
        "/users/login",
        json={
            "email": "customer@example.com",
            "password": "correct-horse-battery",
        },
    ).json()["access_token"]

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert customer.id > 0
    assert response.status_code == 403


def test_admin_directory_filters_and_paginates_without_passwords(client, db):
    create_user(db, "Admin", "admin@example.com", "admin")
    create_user(db, "Customer One", "customer1@example.com", "user")
    create_user(db, "Customer Two", "customer2@example.com", "user")
    create_user(db, "Agent", "agent@example.com", "support_agent")
    token = client.post(
        "/users/login",
        json={
            "email": "admin@example.com",
            "password": "correct-horse-battery",
        },
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first_page = client.get("/users?page=1&limit=2", headers=headers)
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 4
    assert len(first_page.json()["items"]) == 2
    assert all("password" not in item for item in first_page.json()["items"])

    customers = client.get("/users?role=user", headers=headers)
    assert customers.status_code == 200
    assert customers.json()["total"] == 2
    assert {item["role"] for item in customers.json()["items"]} == {"user"}

    agents = client.get("/users?role=support_agent", headers=headers)
    assert agents.status_code == 200
    assert [item["email"] for item in agents.json()["items"]] == ["agent@example.com"]

import pytest
from httpx import AsyncClient

from app.domain import models

pytestmark = pytest.mark.asyncio


async def auth_header(client: AsyncClient, gym: models.Gym) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": gym.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_customer(client: AsyncClient, headers: dict[str, str], email: str, active: bool = True, first_name: str = "Alex") -> dict:
    payload = {
        "first_name": first_name,
        "last_name": "Doe",
        "email": email,
        "active": active,
        "phone": "1234567890",
    }
    response = await client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def test_create_customer(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    payload = {
        "first_name": "Jamie",
        "last_name": "Smith",
        "email": "jamie@example.com",
        "active": True,
    }

    response = await client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == payload["first_name"]
    assert data["email"] == payload["email"]


async def test_list_customers_with_filters(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    await create_customer(client, headers, "active@example.com", active=True, first_name="Alex")
    await create_customer(client, headers, "inactive@example.com", active=False, first_name="Taylor")

    active_response = await client.get("/api/v1/customers", params={"active": False}, headers=headers)
    assert active_response.status_code == 200
    active_data = active_response.json()
    assert len(active_data) == 1
    assert active_data[0]["email"] == "inactive@example.com"

    search_response = await client.get("/api/v1/customers", params={"q": "Alex"}, headers=headers)
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert len(search_data) == 1

    email_search = await client.get("/api/v1/customers", params={"q": "inactive@example.com"}, headers=headers)
    assert email_search.status_code == 200
    email_matches = email_search.json()
    assert len(email_matches) == 1
    assert email_matches[0]["email"] == "inactive@example.com"


async def test_get_update_delete_customer(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    created = await create_customer(client, headers, "member@example.com")
    customer_id = created["id"]

    fetch = await client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert fetch.status_code == 200

    update_response = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"first_name": "Jordan", "active": False},
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["first_name"] == "Jordan"
    assert updated["active"] is False

    delete_response = await client.delete(f"/api/v1/customers/{customer_id}", headers=headers)
    assert delete_response.status_code == 204

    fetch_after_delete = await client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert fetch_after_delete.status_code == 404


async def test_customer_access_restricted_to_owner(client: AsyncClient, create_gym: models.Gym) -> None:
    headers_owner = await auth_header(client, create_gym)
    created = await create_customer(client, headers_owner, "secure@example.com")

    payload = {
        "name": "Uptown Gym",
        "email": "uptown@example.com",
        "password": "Password123",
        "monthly_fee_cents": 9900,
        "currency": "USD",
    }
    signup = await client.post("/api/v1/auth/signup", json=payload)
    assert signup.status_code == 201

    second_login = await client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    second_token = second_login.json()["access_token"]
    headers_other = {"Authorization": f"Bearer {second_token}"}

    forbidden = await client.get(f"/api/v1/customers/{created['id']}", headers=headers_other)
    assert forbidden.status_code == 404


async def test_customer_requests_require_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/customers",
        json={"first_name": "Nope", "last_name": "User", "email": "nope@example.com"},
    )
    assert response.status_code == 401

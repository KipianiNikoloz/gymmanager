import pytest
from httpx import AsyncClient

from app.core.config import get_api_prefix
from app.domain import models

pytestmark = pytest.mark.asyncio

API_PREFIX = get_api_prefix()


async def auth_header(client: AsyncClient, gym: models.Gym) -> dict[str, str]:
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": gym.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_customer(
    client: AsyncClient,
    headers: dict[str, str],
    email: str,
    *,
    active: bool = True,
    first_name: str = "Alex",
    date_of_birth: str | None = "1990-01-01",
    membership_end: str | None = None,
) -> dict:
    payload = {
        "first_name": first_name,
        "last_name": "Doe",
        "email": email,
        "active": active,
        "phone": "1234567890",
    }
    if date_of_birth is not None:
        payload["date_of_birth"] = date_of_birth
    if membership_end is not None:
        payload["membership_end"] = membership_end
    response = await client.post(f"{API_PREFIX}/customers", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def test_create_customer(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    payload = {
        "first_name": "Jamie",
        "last_name": "Smith",
        "email": "jamie@example.com",
        "active": True,
        "date_of_birth": "1995-05-05",
    }

    response = await client.post(f"{API_PREFIX}/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == payload["first_name"]
    assert data["email"] == payload["email"]
    assert data["date_of_birth"] == payload["date_of_birth"]


async def test_list_customers_with_filters(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    await create_customer(
        client,
        headers,
        "active@example.com",
        active=True,
        first_name="Alex",
        date_of_birth="1990-01-01",
    )
    await create_customer(
        client,
        headers,
        "inactive@example.com",
        active=False,
        first_name="Taylor",
        date_of_birth="1980-01-01",
    )

    active_response = await client.get(f"{API_PREFIX}/customers", params={"active": False}, headers=headers)
    assert active_response.status_code == 200
    active_data = active_response.json()
    assert len(active_data) == 1
    assert active_data[0]["email"] == "inactive@example.com"

    search_response = await client.get(f"{API_PREFIX}/customers", params={"search": "Alex"}, headers=headers)
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert len(search_data) == 1
    assert search_data[0]["email"] == "active@example.com"

    email_search = await client.get(f"{API_PREFIX}/customers", params={"email": "inactive@example.com"}, headers=headers)
    assert email_search.status_code == 200
    email_matches = email_search.json()
    assert len(email_matches) == 1
    assert email_matches[0]["email"] == "inactive@example.com"

    age_response = await client.get(
        f"{API_PREFIX}/customers",
        params={"min_age": 30, "max_age": 50, "limit": 10, "offset": 0},
        headers=headers,
    )
    assert age_response.status_code == 200
    ages = {c["email"] for c in age_response.json()}
    assert ages == {"active@example.com", "inactive@example.com"}


async def test_list_customers_invalid_age_range(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    resp = await client.get(
        f"{API_PREFIX}/customers",
        params={"min_age": 50, "max_age": 10},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "min_age" in resp.json()["detail"]


async def test_list_customers_limit_bounds(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    resp = await client.get(
        f"{API_PREFIX}/customers",
        params={"limit": 1000},
        headers=headers,
    )
    assert resp.status_code == 422

    resp_offset = await client.get(
        f"{API_PREFIX}/customers",
        params={"offset": -1},
        headers=headers,
    )
    assert resp_offset.status_code == 422


async def test_auto_deactivation_on_expiry(client: AsyncClient, create_gym: models.Gym) -> None:
    headers = await auth_header(client, create_gym)
    created = await create_customer(
        client,
        headers,
        "expired@example.com",
        membership_end="2000-01-01",
        active=True,
        date_of_birth=None,
    )
    customer_id = created["id"]

    response = await client.get(f"{API_PREFIX}/customers/{customer_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False


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
    signup = await client.post(f"{API_PREFIX}/auth/signup", json=payload)
    assert signup.status_code == 201

    second_login = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    second_token = second_login.json()["access_token"]
    headers_other = {"Authorization": f"Bearer {second_token}"}

    forbidden = await client.get(f"{API_PREFIX}/customers/{created['id']}", headers=headers_other)
    assert forbidden.status_code == 404


async def test_customer_requests_require_authentication(client: AsyncClient) -> None:
    response = await client.post(
        f"{API_PREFIX}/customers",
        json={"first_name": "Nope", "last_name": "User", "email": "nope@example.com"},
    )
    assert response.status_code == 401

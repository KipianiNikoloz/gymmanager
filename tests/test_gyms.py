import pytest
from httpx import AsyncClient

from app.core.config import get_api_prefix
from app.domain import models

pytestmark = pytest.mark.asyncio

API_PREFIX = get_api_prefix()


async def login_and_get_token(client: AsyncClient, gym: models.Gym) -> str:
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": gym.email, "password": "password123"},
    )
    return response.json()["access_token"]


async def test_get_current_gym(client: AsyncClient, create_gym: models.Gym) -> None:
    token = await login_and_get_token(client, create_gym)
    response = await client.get(
        f"{API_PREFIX}/gyms/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == create_gym.email


async def test_get_current_gym_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{API_PREFIX}/gyms/me")
    assert response.status_code == 401


async def test_get_current_gym_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        f"{API_PREFIX}/gyms/me",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401


async def test_update_current_gym(client: AsyncClient, create_gym: models.Gym) -> None:
    token = await login_and_get_token(client, create_gym)
    payload = {"description": "Now offering 24/7 access", "currency": "EUR"}

    response = await client.patch(
        f"{API_PREFIX}/gyms/me",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == payload["description"]
    assert data["currency"] == payload["currency"]


async def test_delete_current_gym(client: AsyncClient, create_gym: models.Gym) -> None:
    token = await login_and_get_token(client, create_gym)

    response = await client.delete(
        f"{API_PREFIX}/gyms/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    follow_up = await client.get(
        f"{API_PREFIX}/gyms/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_up.status_code == 401

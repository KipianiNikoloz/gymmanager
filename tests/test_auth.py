import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models

pytestmark = pytest.mark.asyncio


async def test_signup_creates_gym(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {
        "name": "Downtown Gym",
        "email": "owner@example.com",
        "password": "Password123",
        "monthly_fee_cents": 7500,
        "currency": "USD",
    }

    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]

    gym = await db_session.get(models.Gym, data["id"])
    assert gym is not None
    assert gym.hashed_password != payload["password"]


async def test_signup_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {
        "name": "Gym A",
        "email": "duplicate@example.com",
        "password": "Password123",
        "monthly_fee_cents": 6000,
        "currency": "USD",
    }
    first = await client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


async def test_login_returns_token(client: AsyncClient, create_gym: models.Gym) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": create_gym.email, "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_rejects_invalid_credentials(client: AsyncClient, create_gym: models.Gym) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": create_gym.email, "password": "wrong"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "missing@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

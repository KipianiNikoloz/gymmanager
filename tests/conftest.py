from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.append(str(ROOT_PATH))

from app.api.deps import get_db
from app.core import mailer as mailer_module
from app.core.security import get_password_hash
from app.db.base import Base
from app.domain import models
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
transport = ASGITransport(app=app)


class _StubMailer(mailer_module.Mailer):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    db_path = TEST_DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def override_dependencies() -> AsyncGenerator[None, None]:
    async def _get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_session
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(autouse=True)
async def reset_tables() -> AsyncGenerator[None, None]:
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(autouse=True)
def stub_mailer(monkeypatch: pytest.MonkeyPatch) -> None:
    original_get_mailer = mailer_module.get_mailer
    original_get_mailer.cache_clear()
    stub = _StubMailer()

    def _get_stub_mailer() -> mailer_module.Mailer:
        return stub

    monkeypatch.setattr(mailer_module, "get_mailer", _get_stub_mailer)
    yield
    monkeypatch.setattr(mailer_module, "get_mailer", original_get_mailer)
    original_get_mailer.cache_clear()


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture()
async def create_gym(db_session: AsyncSession) -> AsyncGenerator[models.Gym, None]:
    gym = models.Gym(
        name="Test Gym",
        email="test@gym.com",
        hashed_password=get_password_hash("password123"),
        monthly_fee_cents=5000,
        currency="USD",
    )
    db_session.add(gym)
    await db_session.commit()
    await db_session.refresh(gym)
    yield gym

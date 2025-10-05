from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain import models, schemas


async def signup_gym(session: AsyncSession, gym_in: schemas.GymCreate) -> models.Gym:
    existing = await session.execute(select(models.Gym).where(models.Gym.email == gym_in.email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Email already registered")

    gym = models.Gym(
        name=gym_in.name,
        email=gym_in.email,
        hashed_password=get_password_hash(gym_in.password),
        address=gym_in.address,
        description=gym_in.description,
        gym_type=gym_in.gym_type,
        monthly_fee_cents=gym_in.monthly_fee_cents,
        currency=gym_in.currency,
    )

    session.add(gym)
    await session.commit()
    await session.refresh(gym)
    return gym


async def authenticate_gym(session: AsyncSession, username: str, password: str) -> str:
    result = await session.execute(select(models.Gym).where(models.Gym.email == username))
    gym = result.scalar_one_or_none()

    if gym is None or not verify_password(password, gym.hashed_password):
        raise ValueError("Incorrect email or password")

    return create_access_token(subject=str(gym.id))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models, schemas


async def update_gym(
    session: AsyncSession,
    gym: models.Gym,
    update: schemas.GymUpdate,
) -> models.Gym:
    updates = update.model_dump(exclude_unset=True)
    if updates:
        for key, value in updates.items():
            setattr(gym, key, value)
        session.add(gym)
        await session.commit()
        await session.refresh(gym)
    return gym


async def delete_gym(session: AsyncSession, gym: models.Gym) -> None:
    # Explicitly remove customers to ensure consistency across backends (e.g., SQLite without FK cascades).
    result = await session.execute(
        select(models.Customer).where(models.Customer.gym_id == gym.id)
    )
    customers = result.scalars().all()
    for customer in customers:
        await session.delete(customer)

    await session.delete(gym)
    await session.commit()

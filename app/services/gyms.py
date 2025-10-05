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
    await session.delete(gym)
    await session.commit()

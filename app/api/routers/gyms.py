from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_gym, get_db
from app.domain import models, schemas

router = APIRouter(prefix="/api/v1/gyms", tags=["gyms"])


@router.get("/me", response_model=schemas.GymOut)
async def read_current_gym(current_gym: models.Gym = Depends(get_current_gym)) -> schemas.GymOut:
    return current_gym


@router.patch("/me", response_model=schemas.GymOut)
async def update_current_gym(
    gym_update: schemas.GymUpdate,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.GymOut:
    updates = gym_update.model_dump(exclude_unset=True)
    if not updates:
        return current_gym

    for key, value in updates.items():
        setattr(current_gym, key, value)

    session.add(current_gym)
    await session.commit()
    await session.refresh(current_gym)
    return current_gym


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_gym(
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> None:
    await session.delete(current_gym)
    await session.commit()

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_gym, get_db
from app.domain import models, schemas
from app.services import gyms as gym_service

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
    updated = await gym_service.update_gym(session, current_gym, gym_update)
    return updated


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_gym(
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> None:
    await gym_service.delete_gym(session, current_gym)

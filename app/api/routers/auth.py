from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain import models, schemas

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.GymOut, status_code=status.HTTP_201_CREATED)
async def signup(
    gym_in: schemas.GymCreate,
    session: AsyncSession = Depends(get_db),
) -> schemas.GymOut:
    existing = await session.execute(select(models.Gym).where(models.Gym.email == gym_in.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    gym = models.Gym(
        name=gym_in.name,
        email=gym_in.email,
        hashed_password=get_password_hash(gym_in.password),
        address=gym_in.address,
        monthly_fee_cents=gym_in.monthly_fee_cents,
        currency=gym_in.currency,
    )

    session.add(gym)
    await session.commit()
    await session.refresh(gym)
    return gym


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> schemas.Token:
    result = await session.execute(select(models.Gym).where(models.Gym.email == form_data.username))
    gym = result.scalar_one_or_none()

    if gym is None or not verify_password(form_data.password, gym.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    token = create_access_token(subject=str(gym.id))
    return schemas.Token(access_token=token)

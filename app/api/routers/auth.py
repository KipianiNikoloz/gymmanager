from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.domain import schemas
from app.services import auth as auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.GymOut, status_code=status.HTTP_201_CREATED)
async def signup(
    gym_in: schemas.GymCreate,
    session: AsyncSession = Depends(get_db),
) -> schemas.GymOut:
    try:
        gym = await auth_service.signup_gym(session, gym_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return gym


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> schemas.Token:
    try:
        token = await auth_service.authenticate_gym(session, form_data.username, form_data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return schemas.Token(access_token=token)

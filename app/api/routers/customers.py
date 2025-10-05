from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_gym, get_db
from app.domain import models, schemas
from app.services import customers as customer_service

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post("", response_model=schemas.CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: schemas.CustomerCreate,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = await customer_service.create_customer(session, current_gym, customer_in)
    return customer


@router.get("", response_model=list[schemas.CustomerOut])
async def list_customers(
    active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, min_length=1),
    first_name: Optional[str] = Query(default=None, min_length=1),
    last_name: Optional[str] = Query(default=None, min_length=1),
    email: Optional[str] = Query(default=None, min_length=3),
    min_age: Optional[int] = Query(default=None, ge=0),
    max_age: Optional[int] = Query(default=None, ge=0),
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> list[schemas.CustomerOut]:
    customers = await customer_service.list_customers(
        session,
        current_gym.id,
        active=active,
        search=search,
        first_name=first_name,
        last_name=last_name,
        email=email,
        min_age=min_age,
        max_age=max_age,
    )
    return customers


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
async def get_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = await customer_service.get_customer(session, current_gym.id, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=schemas.CustomerOut)
async def update_customer(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = await customer_service.update_customer(session, current_gym.id, customer_id, customer_update)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> None:
    deleted = await customer_service.delete_customer(session, current_gym.id, customer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

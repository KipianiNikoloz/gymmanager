from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_gym, get_db
from app.core.mailer import get_mailer
from app.domain import models, schemas

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post("", response_model=schemas.CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: schemas.CustomerCreate,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = models.Customer(
        gym_id=current_gym.id,
        **customer_in.model_dump(exclude_unset=True),
    )
    session.add(customer)
    await session.commit()
    await session.refresh(customer)

    mailer = get_mailer()
    gym_name = current_gym.name or "our gym"
    subject = f"Welcome to {gym_name}!"
    body_lines = [
        f"Hi {customer.first_name},",
        "",
        f"Welcome to {gym_name}. We're excited to see you in the club!",
        "Here’s what you can do next:",
        "  • Check in at the front desk on your first visit.",
        "  • Ask our staff about class schedules and membership perks.",
        "  • Reach out any time—you can reply directly to this email.",
        "",
        "See you soon!",
        f"{gym_name} Team",
    ]
    await mailer.send(to=customer.email, subject=subject, body="\n".join(body_lines))

    return customer


@router.get("", response_model=list[schemas.CustomerOut])
async def list_customers(
    active: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None, min_length=1),
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> list[schemas.CustomerOut]:
    stmt = select(models.Customer).where(models.Customer.gym_id == current_gym.id)

    if active is not None:
        stmt = stmt.where(models.Customer.active == active)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                models.Customer.first_name.ilike(pattern),
                models.Customer.last_name.ilike(pattern),
                models.Customer.email.ilike(pattern),
            )
        )

    result = await session.execute(stmt.order_by(models.Customer.created_at.desc()))
    return result.scalars().all()


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
async def get_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = await session.get(models.Customer, customer_id)
    if customer is None or customer.gym_id != current_gym.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=schemas.CustomerOut)
async def update_customer(
    customer_id: int,
    customer_update: schemas.CustomerUpdate,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> schemas.CustomerOut:
    customer = await session.get(models.Customer, customer_id)
    if customer is None or customer.gym_id != current_gym.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    updates = customer_update.model_dump(exclude_unset=True)
    if updates:
        for key, value in updates.items():
            setattr(customer, key, value)
        session.add(customer)
        await session.commit()
        await session.refresh(customer)

    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
    current_gym: models.Gym = Depends(get_current_gym),
) -> None:
    customer = await session.get(models.Customer, customer_id)
    if customer is None or customer.gym_id != current_gym.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    await session.delete(customer)
    await session.commit()

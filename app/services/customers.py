from datetime import date
from typing import Iterable, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mailer import get_mailer
from app.domain import models, schemas

def _today() -> date:
    return date.today()


def _calculate_age(dob: Optional[date]) -> Optional[int]:
    if dob is None:
        return None
    today = _today()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return years


async def _deactivate_if_expired(customers: Iterable[models.Customer], session: AsyncSession) -> None:
    today = _today()
    changed = False
    expired_ids: list[int] = []
    for customer in customers:
        if customer.membership_end and customer.membership_end < today and customer.active:
            customer.active = False
            session.add(customer)
            changed = True
            expired_ids.append(customer.id)
    if changed:
        await session.commit()
        for customer in customers:
            if customer.id in expired_ids:
                await session.refresh(customer)


def _apply_age_filters(customers: list[models.Customer], min_age: Optional[int], max_age: Optional[int]) -> list[models.Customer]:
    if min_age is None and max_age is None:
        return customers

    filtered: list[models.Customer] = []
    for customer in customers:
        age = _calculate_age(customer.date_of_birth)
        if age is None:
            continue
        if min_age is not None and age < min_age:
            continue
        if max_age is not None and age > max_age:
            continue
        filtered.append(customer)
    return filtered


async def create_customer(
    session: AsyncSession,
    gym: models.Gym,
    customer_in: schemas.CustomerCreate,
) -> models.Customer:
    customer = models.Customer(
        gym_id=gym.id,
        **customer_in.model_dump(exclude_unset=True),
    )
    session.add(customer)
    await session.commit()
    await session.refresh(customer)

    mailer = get_mailer()
    gym_name = gym.name or "our gym"
    body_lines = [
        f"Hi {customer.first_name},",
        "",
        f"Welcome to {gym_name}. We're excited to see you in the club!",
        "Here's what you can do next:",
        "  - Check in at the front desk on your first visit.",
        "  - Ask our staff about class schedules and membership perks.",
        "  - Reach out any time—you can reply directly to this email.",
        "",
        "See you soon!",
        f"{gym_name} Team",
    ]
    await mailer.send(
        to=customer.email,
        subject=f"Welcome to {gym_name}!",
        body="\n".join(body_lines),
    )

    return customer


async def list_customers(
    session: AsyncSession,
    gym_id: int,
    *,
    active: Optional[bool] = None,
    search: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
) -> list[models.Customer]:
    stmt = select(models.Customer).where(models.Customer.gym_id == gym_id)

    if active is not None:
        stmt = stmt.where(models.Customer.active == active)

    def _ilike(value: str) -> str:
        return f"%{value}%"

    if search:
        pattern = _ilike(search)
        stmt = stmt.where(
            or_(
                models.Customer.first_name.ilike(pattern),
                models.Customer.last_name.ilike(pattern),
                models.Customer.email.ilike(pattern),
            )
        )

    if first_name:
        stmt = stmt.where(models.Customer.first_name.ilike(_ilike(first_name)))

    if last_name:
        stmt = stmt.where(models.Customer.last_name.ilike(_ilike(last_name)))

    if email:
        stmt = stmt.where(models.Customer.email.ilike(_ilike(email)))

    result = await session.execute(stmt.order_by(models.Customer.created_at.desc()))
    customers: list[models.Customer] = list(result.scalars().all())

    customers = _apply_age_filters(customers, min_age, max_age)
    await _deactivate_if_expired(customers, session)
    return customers


async def get_customer(
    session: AsyncSession,
    gym_id: int,
    customer_id: int,
) -> Optional[models.Customer]:
    customer = await session.get(models.Customer, customer_id)
    if customer is None or customer.gym_id != gym_id:
        return None

    await _deactivate_if_expired([customer], session)
    return customer


async def update_customer(
    session: AsyncSession,
    gym_id: int,
    customer_id: int,
    update: schemas.CustomerUpdate,
) -> Optional[models.Customer]:
    customer = await get_customer(session, gym_id, customer_id)
    if customer is None:
        return None

    updates = update.model_dump(exclude_unset=True)
    if updates:
        for key, value in updates.items():
            setattr(customer, key, value)
        session.add(customer)
        await session.commit()
        await session.refresh(customer)

    await _deactivate_if_expired([customer], session)
    return customer


async def delete_customer(
    session: AsyncSession,
    gym_id: int,
    customer_id: int,
) -> bool:
    customer = await session.get(models.Customer, customer_id)
    if customer is None or customer.gym_id != gym_id:
        return False

    await session.delete(customer)
    await session.commit()
    return True

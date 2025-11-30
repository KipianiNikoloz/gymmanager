import asyncio
from datetime import date
from typing import Iterable, Optional, Callable, Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mailer import get_mailer
from app.domain import models, schemas


def _today() -> date:
    return date.today()


def _years_ago(years: int) -> date:
    today = _today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        # Handle leap day by clamping to Feb 28.
        return today.replace(month=2, day=28, year=today.year - years)


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

async def create_customer(
    session: AsyncSession,
    gym: models.Gym,
    customer_in: schemas.CustomerCreate,
    schedule_mail: Callable[[Callable[..., Any], Any, Any], Any] | None = None,
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
    if schedule_mail:
        maybe_task = schedule_mail(mailer.send, customer.email, f"Welcome to {gym_name}!", "\n".join(body_lines))
        if asyncio.iscoroutine(maybe_task) or isinstance(maybe_task, asyncio.Task):
            await maybe_task
    else:
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
    limit: int = 50,
    offset: int = 0,
) -> list[models.Customer]:
    if min_age is not None and max_age is not None and min_age > max_age:
        raise ValueError("min_age cannot be greater than max_age")

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

    if min_age is not None:
        min_dob = _years_ago(min_age)
        stmt = stmt.where(models.Customer.date_of_birth <= min_dob)

    if max_age is not None:
        max_dob = _years_ago(max_age)
        stmt = stmt.where(models.Customer.date_of_birth >= max_dob)

    stmt = stmt.order_by(models.Customer.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    customers: list[models.Customer] = list(result.scalars().all())

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

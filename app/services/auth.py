import asyncio
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import mailer as mailer_module
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain import models, schemas

logger = logging.getLogger(__name__)


async def signup_gym(
    session: AsyncSession,
    gym_in: schemas.GymCreate,
    schedule_mail: Callable[[Callable[..., Any], Any, Any], Any] | None = None,
) -> models.Gym:
    existing = await session.execute(select(models.Gym).where(models.Gym.email == gym_in.email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Email already registered")

    gym = models.Gym(
        name=gym_in.name,
        email=gym_in.email,
        hashed_password=get_password_hash(gym_in.password),
        address=gym_in.address,
        description=gym_in.description,
        gym_type=gym_in.gym_type,
        monthly_fee_cents=gym_in.monthly_fee_cents,
        currency=gym_in.currency,
    )

    session.add(gym)
    await session.commit()
    await session.refresh(gym)

    # Send welcome email; failures are logged but do not block signup.
    try:
        mailer = mailer_module.get_mailer()
        subject = "Welcome to your Gym Dashboard!"
        body_lines = [
            f"Hi {gym.name},",
            "",
            "Your gym account has been created successfully.",
            "Here are a few quick tips to get started:",
            "  • Use your email to log in from the dashboard.",
            "  • Invite your trainers and staff to collaborate.",
            "  • Add customers to begin tracking memberships.",
            "",
            "We're glad to have you with us!",
            "The Gym Manager Team",
        ]
        if schedule_mail:
            maybe_task = schedule_mail(mailer.send, gym.email, subject, "\n".join(body_lines))
            if asyncio.iscoroutine(maybe_task) or isinstance(maybe_task, asyncio.Task):
                await maybe_task
        else:
            await mailer.send(to=gym.email, subject=subject, body="\n".join(body_lines))
    except Exception:
        logger.exception("Failed to send welcome email to gym %s", gym.email)

    return gym


async def authenticate_gym(session: AsyncSession, username: str, password: str) -> str:
    result = await session.execute(select(models.Gym).where(models.Gym.email == username))
    gym = result.scalar_one_or_none()

    if gym is None or not verify_password(password, gym.hashed_password):
        raise ValueError("Incorrect email or password")

    return create_access_token(subject=str(gym.id))

import pytest
from datetime import date, timedelta

from app.domain import schemas
from app.services import auth as auth_service
from app.services import customers as customer_service
from app.services import gyms as gym_service


pytestmark = pytest.mark.asyncio


async def test_signup_gym_hashes_password_and_sends_mail(db_session, mailer_stub) -> None:
    gym_in = schemas.GymCreate(
        name="Service Gym",
        email="nikolozkipiani@icloud.com",
        password="Password123",
        monthly_fee_cents=5000,
        currency="USD",
    )

    gym = await auth_service.signup_gym(db_session, gym_in, schedule_mail=mailer_stub.add_task)

    assert gym.id is not None
    assert gym.hashed_password != gym_in.password
    assert len(mailer_stub.sent) == 1
    sent_to, subject, body = mailer_stub.sent[0]
    assert sent_to == gym_in.email
    assert "Welcome" in subject
    assert gym_in.name in body


async def test_signup_gym_rejects_duplicate_email(db_session) -> None:
    gym_in = schemas.GymCreate(
        name="Dup Gym",
        email="dup@example.com",
        password="Password123",
        monthly_fee_cents=4000,
        currency="USD",
    )
    await auth_service.signup_gym(db_session, gym_in)

    with pytest.raises(ValueError):
        await auth_service.signup_gym(db_session, gym_in)


async def test_authenticate_gym_success_and_failure(db_session) -> None:
    gym_in = schemas.GymCreate(
        name="Auth Gym",
        email="auth@example.com",
        password="Password123",
        monthly_fee_cents=3000,
        currency="USD",
    )
    gym = await auth_service.signup_gym(db_session, gym_in)

    token = await auth_service.authenticate_gym(db_session, gym.email, "Password123")
    assert token

    with pytest.raises(ValueError):
        await auth_service.authenticate_gym(db_session, gym.email, "wrongpassword")


async def test_list_customers_filters_by_age_and_auto_deactivates(db_session, create_gym) -> None:
    gym = create_gym
    # Older customer (45 years)
    await customer_service.create_customer(
        db_session,
        gym,
        schemas.CustomerCreate(
            first_name="Alex",
            last_name="Old",
            email="old@example.com",
            active=True,
            date_of_birth=date.today() - timedelta(days=45 * 365),
        ),
    )
    # Younger customer (20 years) with expired membership to trigger auto-deactivation
    expired_customer = await customer_service.create_customer(
        db_session,
        gym,
        schemas.CustomerCreate(
            first_name="Casey",
            last_name="Young",
            email="young@example.com",
            active=True,
            date_of_birth=date.today() - timedelta(days=20 * 365),
            membership_end=date.today() - timedelta(days=1),
        ),
    )

    results = await customer_service.list_customers(
        db_session,
        gym_id=gym.id,
        min_age=30,
        max_age=50,
        limit=10,
        offset=0,
    )
    emails = {c.email for c in results}
    assert "old@example.com" in emails
    assert "young@example.com" not in emails

    refreshed = await customer_service.get_customer(db_session, gym.id, expired_customer.id)
    assert refreshed is not None
    assert refreshed.active is False


async def test_list_customers_supports_pagination(db_session, create_gym) -> None:
    gym = create_gym
    first = await customer_service.create_customer(
        db_session,
        gym,
        schemas.CustomerCreate(
            first_name="First",
            last_name="User",
            email="first@example.com",
        ),
    )
    second = await customer_service.create_customer(
        db_session,
        gym,
        schemas.CustomerCreate(
            first_name="Second",
            last_name="User",
            email="second@example.com",
        ),
    )

    page_one = await customer_service.list_customers(db_session, gym.id, limit=1, offset=0)
    page_two = await customer_service.list_customers(db_session, gym.id, limit=1, offset=1)

    assert len(page_one) == 1
    assert len(page_two) == 1
    # Ordered by created_at desc, second was created last.
    assert page_one[0].email == second.email
    assert page_two[0].email == first.email


async def test_delete_gym_cascades_customers(db_session, create_gym) -> None:
    gym = create_gym
    await customer_service.create_customer(
        db_session,
        gym,
        schemas.CustomerCreate(
            first_name="To",
            last_name="Delete",
            email="cascade@example.com",
        ),
    )

    await gym_service.delete_gym(db_session, gym)

    # Customers are deleted via cascade; fetching list should be empty.
    remaining = await customer_service.list_customers(db_session, gym.id)
    assert remaining == []

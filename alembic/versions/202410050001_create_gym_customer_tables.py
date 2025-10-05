from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "202410050001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gyms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("monthly_fee_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_gyms_email"),
    )
    op.create_index("ix_gyms_email", "gyms", ["email"], unique=False)
    op.create_index("ix_gyms_id", "gyms", ["id"], unique=False)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gym_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("membership_start", sa.Date(), nullable=True),
        sa.Column("membership_end", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_customers_email", "customers", ["email"], unique=False)
    op.create_index("ix_customers_gym_id", "customers", ["gym_id"], unique=False)
    op.create_index("ix_customers_id", "customers", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_customers_id", table_name="customers")
    op.drop_index("ix_customers_gym_id", table_name="customers")
    op.drop_index("ix_customers_email", table_name="customers")
    op.drop_table("customers")

    op.drop_index("ix_gyms_id", table_name="gyms")
    op.drop_index("ix_gyms_email", table_name="gyms")
    op.drop_table("gyms")

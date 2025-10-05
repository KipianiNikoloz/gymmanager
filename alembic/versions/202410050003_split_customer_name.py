from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "202410050003"
down_revision: Union[str, None] = "202410050002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("first_name", sa.String(length=128), nullable=False, server_default=""),
    )
    op.add_column(
        "customers",
        sa.Column("last_name", sa.String(length=128), nullable=False, server_default=""),
    )

    op.execute("UPDATE customers SET first_name = full_name, last_name = ''")

    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.alter_column(
            "first_name",
            existing_type=sa.String(length=128),
            server_default=None,
            existing_server_default="",
        )
        batch_op.alter_column(
            "last_name",
            existing_type=sa.String(length=128),
            server_default=None,
            existing_server_default="",
        )
        batch_op.drop_column("full_name")


def downgrade() -> None:
    op.add_column("customers", sa.Column("full_name", sa.String(length=255), nullable=False, server_default=""))
    op.execute("UPDATE customers SET full_name = trim(first_name || ' ' || last_name)")

    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.drop_column("last_name")
        batch_op.drop_column("first_name")

    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.alter_column(
            "full_name",
            existing_type=sa.String(length=255),
            server_default=None,
            existing_server_default="",
        )

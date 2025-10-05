from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "202410050004"
down_revision: Union[str, None] = "202410050003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("date_of_birth", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "date_of_birth")

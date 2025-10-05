from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "202410050002"
down_revision: Union[str, None] = "202410050001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("gyms", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("gyms", sa.Column("gym_type", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("gyms", "gym_type")
    op.drop_column("gyms", "description")

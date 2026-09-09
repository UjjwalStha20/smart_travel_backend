"""make user_trips.route_id nullable

User trips can target attracton destinations which have no trekking route,
so route_id must be optional.

Revision ID: a1b2c3d4e5f6
Revises: d0edc8b86582
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd0edc8b86582'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('user_trips', 'route_id', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user_trips', 'route_id', nullable=False)
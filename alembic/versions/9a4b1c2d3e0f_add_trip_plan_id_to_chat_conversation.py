"""add trip_plan_id to chat conversation

Revision ID: 9a4b1c2d3e0f
Revises: 62c863dee937
Create Date: 2026-09-09 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a4b1c2d3e0f'
down_revision: Union[str, Sequence[str], None] = '62c863dee937'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'chat_conversation',
        sa.Column('trip_plan_id', sa.Uuid(), nullable=True),
    )
    op.create_index(
        'ix_chat_conversation_user_id',
        'chat_conversation',
        ['user_id'],
    )
    op.create_foreign_key(
        'fk_chat_conversation_trip_plan_id_trip_plans',
        'chat_conversation',
        'trip_plans',
        ['trip_plan_id'],
        ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_chat_conversation_trip_plan_id_trip_plans',
        'chat_conversation',
        type_='foreignkey',
    )
    op.drop_index('ix_chat_conversation_user_id', table_name='chat_conversation')
    op.drop_column('chat_conversation', 'trip_plan_id')
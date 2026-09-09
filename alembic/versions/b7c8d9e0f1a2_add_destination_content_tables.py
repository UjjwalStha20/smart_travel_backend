"""add_destination_content_tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('destination_highlight',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('distance_hint', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('visit_time', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_destination_highlight_destination_id'), 'destination_highlight', ['destination_id'], unique=False)
    op.create_table('destination_thing_to_do',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('duration', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('difficulty', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('cost', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_destination_thing_to_do_destination_id'), 'destination_thing_to_do', ['destination_id'], unique=False)
    op.create_table('destination_faq',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('question', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('answer', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_destination_faq_destination_id'), 'destination_faq', ['destination_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_destination_faq_destination_id'), table_name='destination_faq')
    op.drop_table('destination_faq')
    op.drop_index(op.f('ix_destination_thing_to_do_destination_id'), table_name='destination_thing_to_do')
    op.drop_table('destination_thing_to_do')
    op.drop_index(op.f('ix_destination_highlight_destination_id'), table_name='destination_highlight')
    op.drop_table('destination_highlight')
    # ### end Alembic commands ###

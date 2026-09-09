"""destination types: categories, highlights, detail tables

Revision ID: ae3024fdeb42
Revises: 9a4b1c2d3e0f
Create Date: 2026-09-09 23:40:12.687290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ae3024fdeb42'
down_revision: Union[str, Sequence[str], None] = '9a4b1c2d3e0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_CATEGORY_VALUES = [
    'city', 'hike', 'mountain', 'nature', 'lake', 'waterfall',
    'viewpoint', 'cultural_site', 'religious_site', 'historical_site',
    'wildlife', 'adventure', 'other',
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    # Extend the existing PostgreSQL native enums with new labels.
    existing_categories = {
        row[0] for row in bind.execute(
            sa.text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                    "WHERE pg_type.typname = 'destinationcategory'")
        )
    }
    for value in NEW_CATEGORY_VALUES:
        if value not in existing_categories:
            op.execute(sa.text(f"ALTER TYPE destinationcategory ADD VALUE '{value}'"))

    existing_difficulties = {
        row[0] for row in bind.execute(
            sa.text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                    "WHERE pg_type.typname = 'difficulty'")
        )
    }
    if 'extreme' not in existing_difficulties:
        op.execute(sa.text("ALTER TYPE difficulty ADD VALUE 'extreme'"))

    op.create_table('hike_details',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('difficulty', sa.Enum('easy', 'moderate', 'hard', 'extreme', name='difficulty', _create_events=False), nullable=True),
    sa.Column('duration_hours', sa.Numeric(), nullable=True),
    sa.Column('distance_km', sa.Numeric(), nullable=True),
    sa.Column('elevation_gain', sa.Numeric(), nullable=True),
    sa.Column('highest_elevation', sa.Numeric(), nullable=True),
    sa.Column('starting_point', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ending_point', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('estimated_hiking_time', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('guide_recommended', sa.Boolean(), nullable=False),
    sa.Column('required_permits', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('trail_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('water_availability', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('accommodation_available', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('route_description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hike_details_destination_id'), 'hike_details', ['destination_id'], unique=True)
    op.create_table('mountain_details',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('elevation', sa.Numeric(), nullable=True),
    sa.Column('difficulty', sa.Enum('easy', 'moderate', 'hard', 'extreme', name='difficulty', _create_events=False), nullable=True),
    sa.Column('climbing_season', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('required_permits', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('expedition_required', sa.Boolean(), nullable=False),
    sa.Column('base_camp', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('technical_climbing_required', sa.Boolean(), nullable=False),
    sa.Column('approx_duration', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('guide_required', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mountain_details_destination_id'), 'mountain_details', ['destination_id'], unique=True)
    op.create_table('nature_details',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('visit_duration_hours', sa.Numeric(), nullable=True),
    sa.Column('opening_hours', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('difficulty_if_hiking', sa.Enum('easy', 'moderate', 'hard', 'extreme', name='difficulty', _create_events=False), nullable=True),
    sa.Column('distance_from_nearest_major_location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('accessibility', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('best_viewing_season', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('activities', sa.JSON(), nullable=True),
    sa.Column('safety_considerations', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nature_details_destination_id'), 'nature_details', ['destination_id'], unique=True)
    op.create_table('trek_details',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('destination_id', sa.Uuid(), nullable=False),
    sa.Column('duration_days', sa.Integer(), nullable=True),
    sa.Column('distance_km', sa.Numeric(), nullable=True),
    sa.Column('max_elevation', sa.Numeric(), nullable=True),
    sa.Column('elevation_gain', sa.Numeric(), nullable=True),
    sa.Column('difficulty', sa.Enum('easy', 'moderate', 'hard', 'extreme', name='difficulty', _create_events=False), nullable=True),
    sa.Column('best_season', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('start_point', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('end_point', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('required_permits', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('guide_required', sa.Boolean(), nullable=False),
    sa.Column('guide_recommended', sa.Boolean(), nullable=False),
    sa.Column('accommodation_type', sa.Enum('tea_house', 'lodge', 'camping', 'mixed', name='accommodationtype'), nullable=True),
    sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trek_details_destination_id'), 'trek_details', ['destination_id'], unique=True)
    op.add_column('destination', sa.Column('highlights', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")))
    op.add_column('photos', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    op.drop_column('photos', 'is_featured')
    op.drop_column('destination', 'highlights')
    op.drop_index(op.f('ix_trek_details_destination_id'), table_name='trek_details')
    op.drop_table('trek_details')
    op.drop_index(op.f('ix_nature_details_destination_id'), table_name='nature_details')
    op.drop_table('nature_details')
    op.drop_index(op.f('ix_mountain_details_destination_id'), table_name='mountain_details')
    op.drop_table('mountain_details')
    op.drop_index(op.f('ix_hike_details_destination_id'), table_name='hike_details')
    op.drop_table('hike_details')

    categories_in_use = bind.execute(
        sa.text(
            "SELECT count(*) FROM destination "
            "WHERE category IN ('city','hike','mountain','nature','lake','waterfall',"
            "'viewpoint','cultural_site','religious_site','historical_site','wildlife','adventure','other')"
        )
    ).scalar()
    if categories_in_use == 0:
        for value in NEW_CATEGORY_VALUES:
            op.execute(sa.text(f"ALTER TYPE destinationcategory DROP VALUE '{value}'"))

    extreme_in_use = bind.execute(
        sa.text(
            "WITH diffs AS ("
            "SELECT difficulty AS d FROM trekking_routes "
            "UNION ALL SELECT difficulty FROM trek_details "
            "UNION ALL SELECT difficulty FROM hike_details "
            "UNION ALL SELECT difficulty FROM mountain_details "
            "UNION ALL SELECT difficulty_if_hiking FROM nature_details"
            ") SELECT count(*) FROM diffs WHERE d = 'extreme'"
        )
    ).scalar()
    if extreme_in_use == 0:
        op.execute(sa.text("ALTER TYPE difficulty DROP VALUE 'extreme'"))
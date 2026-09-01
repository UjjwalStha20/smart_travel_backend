"""normalize_destination_best_time

Revision ID: 1d2e3f4a5b6c
Revises: c41fa4cb8529
Create Date: 2026-08-06 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d2e3f4a5b6c'
down_revision: Union[str, Sequence[str], None] = 'c41fa4cb8529'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MONTHS = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}

ABBREV = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "may": "May", "jun": "June", "jul": "July", "aug": "August",
    "sep": "September", "sept": "September", "oct": "October",
    "nov": "November", "dec": "December",
}

FULL = {
    "january": "January", "february": "February", "march": "March",
    "april": "April", "may": "May", "june": "June", "july": "July",
    "august": "August", "september": "September", "october": "October",
    "november": "November", "december": "December",
}


def _normalize(value) -> Union[list, None]:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            import json
            value = json.loads(value)
        except Exception:
            value = [value]
    if not isinstance(value, list):
        return None
    result = []
    seen = set()
    for item in value:
        key = str(item).strip().lower()
        name = FULL.get(key) or ABBREV.get(key)
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result or None


def upgrade() -> None:
    """Normalize existing best_time values to full month names."""
    import json

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, best_time FROM destination WHERE best_time IS NOT NULL")
    ).fetchall()
    for row in rows:
        normalized = _normalize(row.best_time) or []
        bind.execute(
            sa.text("UPDATE destination SET best_time = CAST(:bt AS json) WHERE id = :id"),
            {"bt": json.dumps(normalized), "id": row.id},
        )


def downgrade() -> None:
    """Downgrade is a no-op: prior values are unrecoverable after normalization."""
    pass
"""make user display name unique

Revision ID: c9aea76e7e31
Revises: 83aafbec409b
Create Date: 2026-08-24 20:30:01.241613
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9aea76e7e31"
down_revision: Union[str, Sequence[str], None] = "83aafbec409b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make display names unique case-insensitively."""
    op.create_index(
        "uq_users_display_name_lower",
        "users",
        [sa.text("lower(display_name)")],
        unique=True,
    )


def downgrade() -> None:
    """Remove case-insensitive display-name uniqueness."""
    op.drop_index(
        "uq_users_display_name_lower",
        table_name="users",
    )

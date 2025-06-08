"""Add team_assistant_links table

Revision ID: 2746627bbab2
Revises: dbd0d0e19b70
Create Date: 2025-06-08 06:37:54.061139

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2746627bbab2"
down_revision: Union[str, None] = "dbd0d0e19b70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create team_assistant_links table
    op.create_table(
        "team_assistant_links",
        sa.Column("team_id", sa.String(), nullable=False),
        sa.Column("assistant_id", sa.String(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assistant_id"], ["assistants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "assistant_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop team_assistant_links table
    op.drop_table("team_assistant_links")

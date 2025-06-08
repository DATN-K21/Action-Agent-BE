"""update_apikey_table_to_reference_team

Revision ID: bcec2a934209
Revises: 2746627bbab2
Create Date: 2025-06-08 08:15:03.614884

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bcec2a934209"
down_revision: Union[str, None] = "2746627bbab2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing foreign key and assistant_id column
    with op.batch_alter_table("api_keys") as batch_op:
        batch_op.drop_constraint("fk_api_keys_assistant_id_assistants", type_="foreignkey")
        batch_op.drop_column("assistant_id")

        # Add team_id column and foreign key
        batch_op.add_column(sa.Column("team_id", sa.String(), nullable=False))
        batch_op.create_foreign_key("fk_api_keys_team_id_teams", "teams", ["team_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert the changes
    with op.batch_alter_table("api_keys") as batch_op:
        # Drop team foreign key and column
        batch_op.drop_constraint("fk_api_keys_team_id_teams", type_="foreignkey")
        batch_op.drop_column("team_id")

        # Add back assistant_id column and foreign key
        batch_op.add_column(sa.Column("assistant_id", sa.String(), nullable=False))
        batch_op.create_foreign_key("fk_api_keys_assistant_id_assistants", "assistants", ["assistant_id"], ["id"], ondelete="CASCADE")

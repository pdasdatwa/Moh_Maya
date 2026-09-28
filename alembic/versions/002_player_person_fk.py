"""Add worlds.player_person_id foreign key.

Revision ID: 002_player_person_fk
Revises: 001_initial
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_player_person_fk"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_worlds_player_person_id",
        "worlds",
        "people",
        ["player_person_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_worlds_player_person_id", "worlds", type_="foreignkey")

"""add is_deleted to projects

Revision ID: c1fc7ff7d27a
Revises: 97bb60cde171
Create Date: 2026-08-24 20:37:45.830446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1fc7ff7d27a'
down_revision: Union[str, Sequence[str], None] = '97bb60cde171'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_index(
        op.f("ix_projects_is_deleted"),
        "projects",
        ["is_deleted"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index(
        op.f("ix_projects_is_deleted"),
        table_name="projects",
    )

    op.drop_column("projects", "is_deleted")

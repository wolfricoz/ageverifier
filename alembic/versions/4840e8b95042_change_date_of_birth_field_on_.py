"""change date of birth field on idverification table

Revision ID: 4840e8b95042
Revises: 9d05d8ea958f
Create Date: 2025-08-05 22:42:15.318469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4840e8b95042'
down_revision: Union[str, None] = '9d05d8ea958f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "verification",
        "verifieddob",
        existing_type=sa.DateTime(),
        type_=sa.String(2048),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "verification",
        "verifieddob",
        existing_type=sa.String(2048),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
"""increasing the charvar on ageroles

Revision ID: 36c5aa996d17
Revises: 101cbfdfef98
Create Date: 2026-01-18 01:50:24.530352

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '36c5aa996d17'
down_revision: Union[str, None] = '101cbfdfef98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('age_roles', 'type', existing_type=sa.VARCHAR(length=20), type_=sa.VARCHAR(length=50), existing_nullable=False)


def downgrade() -> None:
    op.alter_column('age_roles', 'type', existing_type=sa.VARCHAR(length=50), type_=sa.VARCHAR(length=20), existing_nullable=False)

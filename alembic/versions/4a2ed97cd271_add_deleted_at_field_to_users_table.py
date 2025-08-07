"""add deleted at field to users table

Revision ID: 4a2ed97cd271
Revises: a01546f1d5aa
Create Date: 2025-02-14 00:14:29.582645

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4a2ed97cd271'
down_revision: Union[str, None] = 'a01546f1d5aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('deleted_at', sa.DateTime, nullable=True, default=None))


def downgrade() -> None:
    op.drop_column('users','deleted_at')

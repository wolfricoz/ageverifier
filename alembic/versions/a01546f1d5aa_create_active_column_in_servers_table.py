"""create active column in servers table

Revision ID: a01546f1d5aa
Revises: 
Create Date: 2024-12-15 20:36:50.017431

"""
from email.policy import default
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean

# revision identifiers, used by Alembic.
revision: str = 'a01546f1d5aa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('servers', sa.Column('active', Boolean, default=False))


def downgrade() -> None:
    op.drop_column('servers', 'active')

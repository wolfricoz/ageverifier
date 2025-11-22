"""adding idmessage to idverification

Revision ID: 50d3ccadbd1a
Revises: ed1c87d614f7
Create Date: 2025-11-11 21:17:20.607979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '50d3ccadbd1a'
down_revision: Union[str, None] = 'ed1c87d614f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    with op.batch_alter_table('verification', schema=None) as batch_op:
        batch_op.add_column(sa.Column('idmessage', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('idmessagecreated', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('verification', schema=None) as batch_op:
        batch_op.drop_column('idmessagecreated')
        batch_op.drop_column('idmessage')
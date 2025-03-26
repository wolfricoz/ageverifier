"""add_server_to_id_check_table

Revision ID: 9d05d8ea958f
Revises: 4a2ed97cd271
Create Date: 2025-03-26 15:29:08.095160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d05d8ea958f'
down_revision: Union[str, None] = '4a2ed97cd271'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass
    op.add_column('verification', sa.Column('server', sa.String(255), nullable=True))

def downgrade() -> None:
    pass
    op.drop_column('verification', 'server')

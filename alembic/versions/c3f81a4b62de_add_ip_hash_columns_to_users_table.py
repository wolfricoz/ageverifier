"""add_ip_hash_columns_to_users_table

Revision ID: c3f81a4b62de
Revises: b7c4e1f9a230
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3f81a4b62de'
down_revision: Union[str, None] = 'b7c4e1f9a230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ip_hash', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('ip_prefix_24', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('ip_prefix_20', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('ip_prefix_16', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('ip_recorded_at', sa.DateTime(timezone=True), nullable=True))
    # ip_hash and ip_prefix_24 are the two the alt lookup queries; ip_recorded_at is
    # scanned by the retention sweep on every run.
    op.create_index('ix_users_ip_hash', 'users', ['ip_hash'])
    op.create_index('ix_users_ip_prefix_24', 'users', ['ip_prefix_24'])
    op.create_index('ix_users_ip_recorded_at', 'users', ['ip_recorded_at'])


def downgrade() -> None:
    op.drop_index('ix_users_ip_recorded_at', table_name='users')
    op.drop_index('ix_users_ip_prefix_24', table_name='users')
    op.drop_index('ix_users_ip_hash', table_name='users')
    op.drop_column('users', 'ip_recorded_at')
    op.drop_column('users', 'ip_prefix_16')
    op.drop_column('users', 'ip_prefix_20')
    op.drop_column('users', 'ip_prefix_24')
    op.drop_column('users', 'ip_hash')

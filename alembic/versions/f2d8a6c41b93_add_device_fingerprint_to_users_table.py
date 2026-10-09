"""add_device_fingerprint_to_users_table

Revision ID: f2d8a6c41b93
Revises: e4a9d2c7b815
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2d8a6c41b93'
down_revision: Union[str, None] = 'e4a9d2c7b815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('device_fingerprint', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('fingerprint_recorded_at', sa.DateTime(timezone=True), nullable=True))
    # device_fingerprint is what the alt lookup queries; fingerprint_recorded_at is
    # scanned by the retention sweep on every run.
    op.create_index('ix_users_device_fingerprint', 'users', ['device_fingerprint'])
    op.create_index('ix_users_fingerprint_recorded_at', 'users', ['fingerprint_recorded_at'])


def downgrade() -> None:
    op.drop_index('ix_users_fingerprint_recorded_at', table_name='users')
    op.drop_index('ix_users_device_fingerprint', table_name='users')
    op.drop_column('users', 'fingerprint_recorded_at')
    op.drop_column('users', 'device_fingerprint')

"""add purge dates table

RMRbot's yearly search forum purge dates: a day and month that repeat every year, announced 7 days
before. checked marks the guild's most recent completed purge. The rows go with the server.

Revision ID: 8f3b2d6e1a47
Revises: 5c8e1a7d3f20
Create Date: 2026-11-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8f3b2d6e1a47'
down_revision: Union[str, None] = '5c8e1a7d3f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # RMRbot creates missing tables itself (create_all) when it starts, so the table can already be there.
    if sa.inspect(op.get_bind()).has_table('purge_dates'):
        return
    op.create_table(
        'purge_dates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('guild', sa.BigInteger(), sa.ForeignKey('servers.guild', ondelete='CASCADE'), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('checked', sa.Boolean(), nullable=False),
        sa.Column('last_purged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('announced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('guild', 'month', 'day', name='uq_purge_dates_guild_month_day'),
    )
    op.create_index('ix_purge_dates_guild', 'purge_dates', ['guild'])


def downgrade() -> None:
    op.drop_index('ix_purge_dates_guild', table_name='purge_dates')
    op.drop_table('purge_dates')

"""add denial reasons table

A server's preset reasons for denying a verification, sent to the member by DM (STR-84). Servers
get the default presets on first use, so nothing is seeded here. The rows go with the server.

Revision ID: 5c8e1a7d3f20
Revises: 9b3e7c2a4d61
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5c8e1a7d3f20'
down_revision: Union[str, None] = '9b3e7c2a4d61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # main.py runs Base.metadata.create_all() on every start, so the table can already be there.
    if sa.inspect(op.get_bind()).has_table('denial_reasons'):
        return
    op.create_table(
        'denial_reasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild', sa.BigInteger(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('message', sa.String(length=1500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['guild'], ['servers.guild'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_denial_reasons_guild_label', 'denial_reasons', ['guild', 'label'], unique=True)


def downgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table('denial_reasons'):
        return
    op.drop_index('ix_denial_reasons_guild_label', table_name='denial_reasons')
    op.drop_table('denial_reasons')

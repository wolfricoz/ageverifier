"""add member notes table

Staff notes on a member, per guild, shown on the approval message (STR-83). Both foreign keys
cascade: notes go with the user on a GDPR removal or the inactivity purge, and with the server.

Revision ID: 9b3e7c2a4d61
Revises: f2d8a6c41b93
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b3e7c2a4d61'
down_revision: Union[str, None] = 'f2d8a6c41b93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # main.py runs Base.metadata.create_all() on every start, so the table can already be there.
    if sa.inspect(op.get_bind()).has_table('member_notes'):
        return
    op.create_table(
        'member_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uid', sa.BigInteger(), nullable=False),
        sa.Column('guild', sa.BigInteger(), nullable=False),
        sa.Column('author', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['uid'], ['users.uid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guild'], ['servers.guild'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_member_notes_guild_uid', 'member_notes', ['guild', 'uid'], unique=False)


def downgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table('member_notes'):
        return
    op.drop_index('ix_member_notes_guild_uid', table_name='member_notes')
    op.drop_table('member_notes')

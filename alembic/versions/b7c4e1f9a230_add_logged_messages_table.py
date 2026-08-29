"""add logged messages table

Tracks the messages the bot posts that contain a user's age or date of birth, so a GDPR
removal can delete them by id instead of scanning the full history of four log channels in
every guild the bot is in.

Revision ID: b7c4e1f9a230
Revises: 0d1dbac6317d
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c4e1f9a230'
down_revision: Union[str, None] = '0d1dbac6317d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: the type is created explicitly in upgrade(). Without this, create_table
# emits a second CREATE TYPE of its own and the migration dies on "type already exists".
LOGGED_MESSAGE_TYPE = postgresql.ENUM('LOBBY_LOG', 'APPROVAL', 'ID_CHECK', 'AGE_LOG',
                                      name='loggedmessagetype', create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    # main.py runs Base.metadata.create_all() on every start, so on a bot that has already
    # booted with this model the table and its enum are there before alembic ever sees them.
    # Without this guard the revision dies on "already exists" - and a failed revision blocks
    # every migration that comes after it.
    if sa.inspect(bind).has_table('logged_messages'):
        return
    LOGGED_MESSAGE_TYPE.create(bind, checkfirst=True)
    op.create_table(
        'logged_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uid', sa.BigInteger(), nullable=False),
        sa.Column('guild', sa.BigInteger(), nullable=False),
        sa.Column('channel', sa.BigInteger(), nullable=False),
        sa.Column('message', sa.BigInteger(), nullable=False),
        sa.Column('type', LOGGED_MESSAGE_TYPE, nullable=False),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['uid'], ['users.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_logged_messages_uid'), 'logged_messages', ['uid'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('logged_messages'):
        return
    op.drop_index(op.f('ix_logged_messages_uid'), table_name='logged_messages')
    op.drop_table('logged_messages')
    LOGGED_MESSAGE_TYPE.drop(bind, checkfirst=True)

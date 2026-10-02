"""add_rmrbot_advert_tables

Revision ID: a7e2c9d4f150
Revises: b7c4e1f9a230
Create Date: 2026-10-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7e2c9d4f150'
down_revision: Union[str, None] = 'b7c4e1f9a230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(inspector, table: str) -> set[str]:
    return {column['name'] for column in inspector.get_columns(table)}


def upgrade() -> None:
    # RMRbot's tables. RMRbot creates missing tables itself (create_all) when it starts, so either can already
    # exist: only what's missing is added.
    inspector = sa.inspect(op.get_bind())
    tables = inspector.get_table_names()

    if 'approvals' not in tables:
        op.create_table(
            'approvals',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('uid', sa.BigInteger(), sa.ForeignKey('users.uid', ondelete='CASCADE'), nullable=False),
            sa.Column('guild', sa.BigInteger(), sa.ForeignKey('servers.guild', ondelete='CASCADE'), nullable=False),
            sa.Column('thread', sa.BigInteger(), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    elif 'content' not in _columns(inspector, 'approvals'):
        # The advert's text as approved; RMRbot diffs later edits against it.
        op.add_column('approvals', sa.Column('content', sa.Text(), nullable=True))

    if 'advertisements' not in tables:
        op.create_table(
            'advertisements',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=False),
            sa.Column('thread_id', sa.BigInteger(), nullable=False),
            sa.Column('forum_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.uid', ondelete='CASCADE'), nullable=False),
            sa.Column('consent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('url', sa.String(255), nullable=True),
            sa.Column('approved', sa.Boolean(), nullable=False),
            sa.Column('deleted', sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index('ix_advertisements_thread_id', 'advertisements', ['thread_id'])
        op.create_index('ix_advertisements_forum_id', 'advertisements', ['forum_id'])
        op.create_index('ix_advertisements_user_id', 'advertisements', ['user_id'])
    elif 'url' not in _columns(inspector, 'advertisements'):
        op.add_column('advertisements', sa.Column('url', sa.String(255), nullable=True))


def downgrade() -> None:
    # approvals predates this revision (RMRbot has used it for years), so only the column added here is removed.
    op.drop_table('advertisements')
    op.drop_column('approvals', 'content')

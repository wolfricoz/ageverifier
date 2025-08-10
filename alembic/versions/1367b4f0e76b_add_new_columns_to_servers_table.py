"""Add new columns to servers table

Revision ID: 1367b4f0e76b
Revises: 4840e8b95042
Create Date: 2025-08-10 01:02:23.044724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = '1367b4f0e76b'
down_revision: Union[str, None] = '4840e8b95042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add a name column to the servers table
    op.add_column('servers', sa.Column('name', sa.String(1024, collation='utf8mb4_unicode_ci'), nullable=True))
    # Add an owner column to the servers table
    op.add_column('servers', sa.Column('owner', sa.String(2048), nullable=True))
    # Add a member_count column with a default of 0
    op.add_column('servers', sa.Column('member_count', sa.BigInteger(), nullable=False, server_default=sa.text('0')))
    # Add an invite column with a default of an empty string
    op.add_column('servers', sa.Column('invite', sa.String(256, collation='utf8mb4_unicode_ci'), nullable=False, server_default=sa.text("''")))
    # Add a created timestamp with a server default
    op.add_column('servers', sa.Column('created', sa.DateTime(timezone=True), nullable=False, server_default=func.now()))
    # Add an updated_at timestamp that auto-updates
    op.add_column('servers', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()))
    # Add a deleted_at timestamp that can be null
    op.add_column('servers', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    # Add a premium boolean column with a default of False
    op.add_column('servers', sa.Column('premium', sa.Boolean(), nullable=False, server_default=sa.text('false')))

def downgrade():
    # Drop all the new columns in the reverse order of creation
    op.drop_column('servers', 'premium')
    op.drop_column('servers', 'deleted_at')
    op.drop_column('servers', 'updated_at')
    op.drop_column('servers', 'created')
    op.drop_column('servers', 'invite')
    op.drop_column('servers', 'member_count')
    op.drop_column('servers', 'owner')
    op.drop_column('servers', 'name')

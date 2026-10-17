"""website_data_indexes_and_reminders

Revision ID: e4a9d2c7b815
Revises: d5b1f8e3a920
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4a9d2c7b815'
down_revision: Union[str, None] = 'd5b1f8e3a920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every uuid ever written is str(uuid4()), which is 36 characters, so shrinking the
    # column cannot truncate anything; Postgres refuses the change outright if it would.
    op.alter_column('website_data', 'uuid',
                    existing_type=sa.String(2048),
                    type_=sa.String(36),
                    existing_nullable=False)
    # The dashboard looks rows up by gid + uuid on every page load; uuid alone is unique,
    # so a unique index on it serves that query without a composite.
    op.create_index('ix_website_data_uuid', 'website_data', ['uuid'], unique=True)
    # WebsiteDataTransactions.check() filters by gid + uid on every verify button click.
    op.create_index('ix_website_data_gid_uid', 'website_data', ['gid', 'uid'])

    # Abandoned link reminder: when the member first opened the page, and when the
    # reminder for the link was handled.
    op.add_column('website_data', sa.Column('opened', sa.DateTime(), nullable=True))
    op.add_column('website_data', sa.Column('reminded', sa.DateTime(), nullable=True))
    op.create_index('ix_website_data_opened', 'website_data', ['opened'])


def downgrade() -> None:
    op.drop_index('ix_website_data_opened', table_name='website_data')
    op.drop_column('website_data', 'reminded')
    op.drop_column('website_data', 'opened')
    op.drop_index('ix_website_data_gid_uid', table_name='website_data')
    op.drop_index('ix_website_data_uuid', table_name='website_data')
    op.alter_column('website_data', 'uuid',
                    existing_type=sa.String(36),
                    type_=sa.String(2048),
                    existing_nullable=False)

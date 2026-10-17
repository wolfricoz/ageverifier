"""merge_rmrbot_advert_tables

Joins the RMRbot advert tables (a7e2c9d4f150, which follows b7c4e1f9a230 as on master) with the IP hash columns
(c3f81a4b62de). A database at either of them, or at b7c4e1f9a230, upgrades from here without skipping the other.

Revision ID: d5b1f8e3a920
Revises: c3f81a4b62de, a7e2c9d4f150
Create Date: 2026-10-02 00:00:00.000000

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'd5b1f8e3a920'
down_revision: Union[str, Sequence[str], None] = ('c3f81a4b62de', 'a7e2c9d4f150')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

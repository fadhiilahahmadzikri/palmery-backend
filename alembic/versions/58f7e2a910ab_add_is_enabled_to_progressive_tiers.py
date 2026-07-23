"""add_is_enabled_to_progressive_tiers

Revision ID: 58f7e2a910ab
Revises: 403c9645092c
Create Date: 2026-07-22 23:52:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '58f7e2a910ab'
down_revision = '403c9645092c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('progressive_tiers', sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False))

def downgrade() -> None:
    op.drop_column('progressive_tiers', 'is_enabled')

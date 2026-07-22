"""use_enums_for_status

Revision ID: 403c9645092c
Revises: 045cb91dcd24
Create Date: 2026-07-19 23:35:28.383895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '403c9645092c'
down_revision: Union[str, Sequence[str], None] = '045cb91dcd24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Migrate PayrollBatches statuses to ongoing / final
    op.execute("UPDATE payroll_batches SET status = 'ongoing' WHERE status IN ('draft', 'generated');")
    op.execute("UPDATE payroll_batches SET status = 'final' WHERE status IN ('approved', 'paid', 'final');")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert PayrollBatches statuses to draft / approved
    op.execute("UPDATE payroll_batches SET status = 'draft' WHERE status = 'ongoing';")
    op.execute("UPDATE payroll_batches SET status = 'approved' WHERE status = 'final';")

"""Expand employee identity data for dual-write rollout."""
from alembic import op


revision = '20260928_03'
down_revision = '20260928_02'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'ALTER TABLE empleado '
        'ADD COLUMN IF NOT EXISTS documento_identidad VARCHAR(30) NULL;'
    )
    op.execute(
        'ALTER TABLE empleado '
        'ADD COLUMN IF NOT EXISTS documento_identidad_v2 VARCHAR(30) NULL;'
    )


def downgrade():
    op.execute(
        'ALTER TABLE empleado '
        'DROP COLUMN IF EXISTS documento_identidad_v2;'
    )
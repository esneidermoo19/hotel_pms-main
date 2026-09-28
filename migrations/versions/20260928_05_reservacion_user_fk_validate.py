"""Validate the reservation-to-user foreign key in a separate deployment."""
from alembic import op


revision = '20260928_05'
down_revision = '20260928_04'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'ALTER TABLE reservacion '
        'VALIDATE CONSTRAINT fk_reservacion_user;'
    )


def downgrade():
    # PostgreSQL cannot revert a validated constraint to NOT VALID.
    pass
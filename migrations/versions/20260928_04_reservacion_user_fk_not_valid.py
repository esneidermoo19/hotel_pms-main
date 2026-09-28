"""Add the reservation-to-user foreign key without scanning old rows."""
from alembic import op


revision = '20260928_04'
down_revision = '20260928_03'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'ALTER TABLE reservacion '
        'ADD CONSTRAINT fk_reservacion_user '
        'FOREIGN KEY (usuario_id) REFERENCES "user" (id) NOT VALID;'
    )


def downgrade():
    op.execute(
        'ALTER TABLE reservacion '
        'DROP CONSTRAINT IF EXISTS fk_reservacion_user;'
    )
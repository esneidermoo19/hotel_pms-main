"""Create the room status index without blocking concurrent writes."""
from alembic import op


revision = '20260928_02'
down_revision = '20260928_01'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute(
            'CREATE INDEX CONCURRENTLY idx_habitacion_estado '
            'ON habitacion (estado);'
        )


def downgrade():
    with op.get_context().autocommit_block():
        op.execute('DROP INDEX CONCURRENTLY IF EXISTS idx_habitacion_estado;')
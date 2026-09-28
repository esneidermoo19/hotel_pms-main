"""Backfill historical invoice audit references in bounded batches."""
from alembic import context, op
import sqlalchemy as sa


revision = '20260928_06'
down_revision = '20260928_05'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'ALTER TABLE factura '
        'ADD COLUMN IF NOT EXISTS referencia_auditoria VARCHAR(64) NULL;'
    )

    if context.is_offline_mode():
        op.execute("""
            DO $migration$
            DECLARE
                max_id BIGINT;
                batch_count INTEGER;
            BEGIN
                SELECT COALESCE(MAX(id), 0) INTO max_id FROM factura;
                LOOP
                    WITH pending_batch AS (
                        SELECT id
                        FROM factura
                        WHERE id <= max_id
                          AND referencia_auditoria IS NULL
                        ORDER BY id
                        LIMIT 100
                    )
                    UPDATE factura AS f
                    SET referencia_auditoria = 'LEGACY-' || pending_batch.id::text
                    FROM pending_batch
                    WHERE f.id = pending_batch.id;

                    GET DIAGNOSTICS batch_count = ROW_COUNT;
                    EXIT WHEN batch_count = 0;
                END LOOP;
            END
            $migration$;
        """)
        return

    with op.get_context().autocommit_block() as connection:
        max_id = connection.execute(
            sa.text('SELECT COALESCE(MAX(id), 0) FROM factura')
        ).scalar_one()
        last_id = 0

        while last_id < max_id:
            batch_ids = connection.execute(
                sa.text("""
                    WITH pending_batch AS (
                        SELECT id
                        FROM factura
                        WHERE id > :last_id
                          AND id <= :max_id
                          AND referencia_auditoria IS NULL
                        ORDER BY id
                        LIMIT :batch_size
                    )
                    UPDATE factura AS f
                    SET referencia_auditoria = 'LEGACY-' || pending_batch.id::text
                    FROM pending_batch
                    WHERE f.id = pending_batch.id
                    RETURNING f.id
                """),
                {
                    'last_id': last_id,
                    'max_id': max_id,
                    'batch_size': 100,
                },
            ).scalars().all()

            if not batch_ids:
                break
            last_id = max(batch_ids)


def downgrade():
    op.execute(
        'ALTER TABLE factura '
        'DROP COLUMN IF EXISTS referencia_auditoria;'
    )
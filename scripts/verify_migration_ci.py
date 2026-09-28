"""Verify the PostgreSQL migration effects in the ephemeral CI database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app import create_app, db


def main():
    app = create_app()
    with app.app_context():
        if db.engine.dialect.name != 'postgresql':
            raise RuntimeError('Migration CI requires PostgreSQL.')

        connection = db.engine.connect()
        try:
            total, populated = connection.execute(text("""
                SELECT COUNT(*), COUNT(referencia_auditoria)
                FROM factura
                WHERE numero_factura LIKE 'MIGRATION-CI-%'
            """)).one()
            has_index = connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = current_schema()
                      AND indexname = 'idx_habitacion_estado'
                )
            """)).scalar_one()
            fk_validated = connection.execute(text("""
                SELECT COALESCE(
                    (SELECT convalidated
                     FROM pg_constraint
                     WHERE conname = 'fk_reservacion_user'
                       AND conrelid = 'reservacion'::regclass),
                    FALSE
                )
            """)).scalar_one()
        finally:
            connection.close()

    if total != 205 or populated != 205 or not has_index or not fk_validated:
        raise RuntimeError(
            'Migration verification failed: '
            f'invoices={populated}/{total}, index={has_index}, fk_validated={fk_validated}'
        )

    print('Migration effects verified: 205/205 invoice backfills, index present, FK validated.')


if __name__ == '__main__':
    main()
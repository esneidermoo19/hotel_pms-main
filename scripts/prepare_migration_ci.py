"""Create a pre-migration PostgreSQL schema and seed legacy invoices for CI."""
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

        db.create_all()
        with db.engine.begin() as connection:
            for statement in (
                'ALTER TABLE "user" DROP COLUMN IF EXISTS telefono_normalizado',
                'DROP INDEX IF EXISTS idx_habitacion_estado',
                'ALTER TABLE empleado DROP COLUMN IF EXISTS documento_identidad_v2',
                'ALTER TABLE empleado DROP COLUMN IF EXISTS documento_identidad',
                'ALTER TABLE reservacion DROP CONSTRAINT IF EXISTS fk_reservacion_user',
                'ALTER TABLE factura DROP COLUMN IF EXISTS referencia_auditoria',
            ):
                connection.execute(text(statement))

            connection.execute(text("""
                INSERT INTO factura (
                    numero_factura,
                    subtotal,
                    total,
                    nombre_cliente,
                    nit_cliente
                )
                SELECT
                    'MIGRATION-CI-' || invoice_number::text,
                    0,
                    0,
                    'CI legacy invoice',
                    '000000000'
                FROM generate_series(1, 205) AS sequence(invoice_number)
            """))

    print('Created legacy schema and seeded 205 historical invoices.')


if __name__ == '__main__':
    main()
"""Read-only PostgreSQL checks to run before applying a schema migration."""
import argparse
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db


PREFLIGHT_SQL = text("""
SELECT pid,
       usename,
       application_name,
       state,
       wait_event_type,
       wait_event,
       pg_blocking_pids(pid) AS blocking_pids,
       EXTRACT(EPOCH FROM (clock_timestamp() - COALESCE(query_start, xact_start)))::int AS age_seconds,
       LEFT(regexp_replace(query, '\\s+', ' ', 'g'), 200) AS query
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid()
  AND backend_type = 'client backend'
  AND (
      cardinality(pg_blocking_pids(pid)) > 0
      OR wait_event_type = 'Lock'
      OR (state = 'active' AND query_start < clock_timestamp() - (:max_age * INTERVAL '1 second'))
      OR (state = 'idle in transaction' AND xact_start < clock_timestamp() - (:max_age * INTERVAL '1 second'))
  )
ORDER BY age_seconds DESC NULLS LAST
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--max-query-seconds',
        type=int,
        default=60,
        help='Umbral para consultas activas/transacciones idle antiguas (default: 60).',
    )
    args = parser.parse_args()
    if args.max_query_seconds < 1:
        parser.error('--max-query-seconds debe ser mayor que cero.')

    app = create_app()
    with app.app_context():
        if db.engine.dialect.name != 'postgresql':
            print('Preflight ERROR: DATABASE_URL debe apuntar a PostgreSQL.', file=sys.stderr)
            return 2

        try:
            with db.engine.connect() as connection:
                findings = connection.execute(
                    PREFLIGHT_SQL,
                    {'max_age': args.max_query_seconds},
                ).mappings().all()
        except Exception as error:
            print(f'Preflight ERROR: no se pudo consultar pg_stat_activity: {error}', file=sys.stderr)
            return 2

    if findings:
        print(f'Preflight ABORTADO: {len(findings)} sesión(es) requieren atención:')
        for row in findings:
            print(
                f"- pid={row['pid']} user={row['usename']} "
                f"app={row['application_name'] or '-'} state={row['state']} "
                f"wait={row['wait_event_type'] or '-'}/{row['wait_event'] or '-'} "
                f"age={row['age_seconds'] or 0}s blocking_pids={row['blocking_pids']} "
                f"query={row['query'] or '-'}"
            )
        return 1

    print('Preflight OK: no se detectaron locks, consultas activas largas ni transacciones idle antiguas.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
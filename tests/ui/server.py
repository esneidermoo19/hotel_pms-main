"""
Servidor Flask dedicado a las pruebas de UI con Playwright.

Arranca la misma aplicación real (``create_app`` de producción) sobre una
base de datos SQLite aislada (``instance/hotel_ui_test.db``) con datos
semilla deterministas. De esta forma las pruebas pueden ejecutarse en
cualquier máquina local y en CI sin tocar la base de datos de desarrollo
(``hotel.db``).

Características:
- CSRF ACTIVADO (igual que producción): el navegador real reenvía el token
  oculto de cada formulario automáticamente.
- Reset automático de la base al arrancar (flag ``--reset``/``--no-reset``)
  para que cada ejecución sea reproducible.
- Usuarios semilla: ``admin_ui`` / ``ui_test_123`` (admin) y
  ``recep_ui`` / ``recep_ui_123`` (recepcionista).

Uso:
    python -m tests.ui.server [--host 127.0.0.1] [--port 5151] [--no-reset]
"""
import argparse
import os
import time

from app import create_app, db
from app.models import ConfigHotel, Habitacion, User

DB_FILENAME = 'hotel_ui_test.db'

HOST_DEFAULT = '127.0.0.1'
PORT_DEFAULT = 5151

UI_ADMIN_USER = os.environ.get('UI_ADMIN_USER', 'admin_ui')
UI_ADMIN_PASS = os.environ.get('UI_ADMIN_PASS', 'ui_test_123')
UI_RECEP_USER = os.environ.get('UI_RECEP_USER', 'recep_ui')
UI_RECEP_PASS = os.environ.get('UI_RECEP_PASS', 'recep_ui_123')


class UIConfig:
    """Configuración de la app para las pruebas de UI (BD aislada)."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FILENAME
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'ui-test-secret-key-playwright'
    MAIL_SUPPRESS_SEND = True


def _seed(app):
    """Crea los datos base necesarios para la navegación y los logins."""
    with app.app_context():
        if not ConfigHotel.query.first():
            db.session.add(ConfigHotel(
                nombre='Hotel Boutique La Orquídea (UI Test)',
                nit='900.123.456-7',
                direccion='Calle 10 #5-30, Centro Histórico',
                ciudad='Bogotá D.C.',
                telefono='+57 601 234 5678',
                email='ui-test@laorquidea.test',
                web='www.laorquidea.test',
            ))

        if not User.query.filter_by(username=UI_ADMIN_USER).first():
            admin = User(username=UI_ADMIN_USER, nombre='Admin UI Test',
                         email='admin-ui@test.com', rol='admin', activo=True)
            admin.password = UI_ADMIN_PASS
            db.session.add(admin)

        if not User.query.filter_by(username=UI_RECEP_USER).first():
            recep = User(username=UI_RECEP_USER, nombre='Recepción UI Test',
                         email='recep-ui@test.com', rol='recepcionista', activo=True)
            recep.password = UI_RECEP_PASS
            db.session.add(recep)

        # Habitación base para ejercitar edición/eliminación desde el listado.
        if not Habitacion.query.filter_by(numero='101').first():
            db.session.add(Habitacion(
                numero='101',
                tipo='Suite',
                precio_noche=250000,
                estado='Disponible',
                cantidad_camas=1,
                tipo_camas='King',
                capacidad_max=2,
            ))

        db.session.commit()


def _reset_db_if_requested(app, reset):
    """Elimina la BD aislada previa para garantizar un arranque determinista."""
    full_path = os.path.join(app.instance_path, DB_FILENAME)
    if reset and os.path.exists(full_path):
        try:
            os.remove(full_path)
            print(f"[ui-server] Base aislada {DB_FILENAME} reiniciada (reset).", flush=True)
        except OSError:
            print(f"[ui-server] AVISO: no se pudo eliminar {full_path}; puede que "
                  "un proceso anterior la tenga abierta.", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Servidor de pruebas de UI (Playwright)')
    parser.add_argument('--host', default=HOST_DEFAULT, help=f'Host de escucha (default {HOST_DEFAULT})')
    parser.add_argument('--port', type=int, default=PORT_DEFAULT, help=f'Puerto (default {PORT_DEFAULT})')
    parser.add_argument('--no-reset', action='store_true',
                        help='No reiniciar la base de datos aislada al arrancar')
    args = parser.parse_args(argv)

    app = create_app(UIConfig)
    _reset_db_if_requested(app, not args.no_reset)

    with app.app_context():
        db.create_all()
    _seed(app)

    print(f"[ui-server] Listo en http://{args.host}:{args.port} "
          f"(BD: {DB_FILENAME}, usuarios semilla: {UI_ADMIN_USER}/{UI_RECEP_USER})",
          flush=True)

    # use_reloader/collectivo desactivados para que el proceso sea un niño
    # controlable por el fixture de sesión (subprocess).
    app.run(host=args.host, port=args.port, debug=False,
            use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
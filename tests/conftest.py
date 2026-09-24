"""
Fixtures globales de la suite de pruebas de Hotel Gema (PMS).

Responsabilidades de este módulo:
- Crear una aplicación Flask aislada en memoria (SQLite) para cada test.
- Exponer el cliente HTTP de pruebas (equivalente a un ``TestClient`` de API).
- Proveer usuarios y recursos base reutilizables con roles bien definidos.
- Reseteo automático del rate limiting para evitar interferencias entre tests.
- Helpers de autenticación reutilizables entre pruebas unitarias y E2E.

Nota de adaptación: el proyecto es una aplicación Flask con formularios
server-side (no una API REST JSON). Por ello los códigos HTTP reales son
302 (POST/Redirect/GET), 200 (render de formularios) y 404 (``get_or_404``).
"""
import pytest
from datetime import datetime, timedelta

from app import create_app, db as _db
from app.models import User, Habitacion, Reservacion, Empleado, ConfigHotel


class TestConfig:
    """Configuración aislada de pruebas (SQLite en memoria, CSRF desactivado)."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-pytest'
    MAIL_SUPPRESS_SEND = True


@pytest.fixture
def app():
    """Inicializa la app Flask y recrea tablas limpias para cada test."""
    _app = create_app(TestConfig)
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """Sesión de base de datos por test (vinculada a la app de pruebas)."""
    yield _db


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Limpia los intentos de rate limiting antes de cada test para evitar interferencias."""
    from app.helpers.security import _failed_attempts
    _failed_attempts.clear()
    yield


@pytest.fixture
def client(app):
    """Cliente HTTP de pruebas de Flask (equivalente funcional a un TestClient)."""
    return app.test_client()


@pytest.fixture
def test_client(client):
    """Alias descriptivo del cliente de pruebas (paridad conceptual con ``TestClient``)."""
    return client


@pytest.fixture
def login_staff(client):
    """Helper que autentica a un usuario del panel staff y devuelve la respuesta."""
    def _login(username: str, password: str):
        return client.post(
            '/staff/login',
            data={'username': username, 'password': password},
            follow_redirects=False,
        )
    return _login


@pytest.fixture
def hotel_config(app, db):
    """Configuración del hotel requerida por rutas que renderizan datos del establecimiento."""
    with app.app_context():
        config = ConfigHotel(
            nombre='Hotel Gema Test',
            nit='900.999.999-9',
            direccion='Calle 1 # 1-1',
            ciudad='Bogotá D.C.',
            telefono='+57 601 000 0000',
            email='test@hotelgema.com',
            nequi_numero='300 000 0000',
            nequi_qr='img/qr_nequi.png',
        )
        db.session.add(config)
        db.session.commit()
        return config


@pytest.fixture
def admin_user(db):
    """Usuario con rol de administrador."""
    user = User(
        username='admin_test',
        email='admin@hotel.com',
        nombre='Administrador Test',
        rol='admin',
        activo=True,
    )
    user.password = 'admin123'
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def recepcion_user(db):
    """Usuario con rol de recepcionista."""
    user = User(
        username='recep_test',
        email='recepcion@hotel.com',
        nombre='Recepcionista Test',
        rol='recepcionista',
        activo=True,
    )
    user.password = 'recep123'
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_habitacion(db):
    """Habitación de prueba disponible para reservas."""
    hab = Habitacion(
        numero='101',
        tipo='Deluxe Suite',
        precio_noche=150000,
        estado='Disponible',
        cantidad_camas=2,
        tipo_camas='King',
        capacidad_max=3,
    )
    db.session.add(hab)
    db.session.commit()
    return hab


@pytest.fixture
def sample_reserva(db, sample_habitacion):
    """Reserva de prueba asociada a una habitación."""
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now(),
        fecha_fin=datetime.now() + timedelta(days=2),
        codigo=Reservacion.generar_codigo(),
        estado='activa',
        nombre_cliente='Juan Pérez',
        email_cliente='juan@ejemplo.com',
        telefono_cliente='3001234567',
        total_pago=300000,
        pagado=True,
    )
    db.session.add(res)
    db.session.commit()
    return res
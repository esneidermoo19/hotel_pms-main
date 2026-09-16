import pytest
from datetime import datetime, timedelta
from app import create_app, db as _db
from app.models import User, Habitacion, Reservacion, Empleado, ConfigHotel

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-pytest'

@pytest.fixture
def app():
    """Fixture que inicializa la aplicación Flask y recrea las tablas limpias para cada test."""
    _app = create_app(TestConfig)
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def db(app):
    """Fixture de sesión de DB por test."""
    yield _db

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Limpia los intentos de rate limiting antes de cada test para evitar interferencias."""
    from app.helpers.security import _failed_attempts
    _failed_attempts.clear()

@pytest.fixture
def client(app):
    """Cliente de pruebas de Flask."""
    return app.test_client()

@pytest.fixture
def admin_user(db):
    """Usuario con rol de administrador."""
    user = User(
        username='admin_test',
        email='admin@hotel.com',
        nombre='Administrador Test',
        rol='admin',
        activo=True
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
        activo=True
    )
    user.password = 'recep123'
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def sample_habitacion(db):
    """Habitación de prueba."""
    hab = Habitacion(
        numero='101',
        tipo='Deluxe Suite',
        precio_noche=150000,
        estado='Disponible',
        cantidad_camas=2,
        tipo_camas='King',
        capacidad_max=3
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
        pagado=True
    )
    db.session.add(res)
    db.session.commit()
    return res

import pytest

from io import BytesIO
from datetime import datetime, timedelta
from app.models import User, Habitacion, Reservacion, ConfigHotel
from app import db

# --- Configuración inicial para los tests ---

@pytest.fixture
def config_hotel(app, db):
    """Fixture para crear la configuración del hotel (requerida para correos/pagos)."""
    with app.app_context():
        config = ConfigHotel(
            nombre='Hotel Test',
            nit='123456789-0',
            email='test@hotel.com',
            nequi_numero='300 123 4567'
        )
        db.session.add(config)
        db.session.commit()
        return config

@pytest.fixture
def cliente_user(app, db):
    """Usuario con rol de cliente."""
    with app.app_context():
        user = User(
            username='cliente_test@ejemplo.com',
            email='cliente_test@ejemplo.com',
            nombre='Cliente Test',
            telefono='3000000000',
            rol='cliente',
            activo=True
        )
        user.password = 'password123'
        db.session.add(user)
        db.session.commit()
        return user


# --- 1. Exploración y Búsqueda ---

def test_home_page(client):
    response = client.get('/huespedes/')
    assert response.status_code == 200

def test_habitaciones_page(client, sample_habitacion):
    response = client.get('/huespedes/habitaciones')
    assert response.status_code == 200
    # Verificar que la habitación de prueba está en la página
    assert sample_habitacion.tipo.encode('utf-8') in response.data
    assert b'150,000' in response.data

# --- 2. Flujo de Reservación ---

def test_crear_reserva_exitosa(client, sample_habitacion, db):
    inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    
    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Test Cliente',
        'email': 'test@ejemplo.com',
        'telefono': '123456789'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verificar en BD
    reserva = Reservacion.query.filter_by(email_cliente='test@ejemplo.com').first()
    assert reserva is not None
    assert reserva.estado == 'pendiente_pago'


def test_validar_fechas_pasadas(client, sample_habitacion):
    inicio = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Test Cliente',
        'email': 'test@ejemplo.com',
        'telefono': '123456789'
    }, follow_redirects=True)
    
    assert b'anterior a hoy' in response.data or b'invalida' in response.data.lower()


def test_habitacion_no_disponible(client, sample_habitacion, sample_reserva):
    # Intentar reservar en fechas que se cruzan con sample_reserva
    inicio = sample_reserva.fecha_inicio.strftime('%Y-%m-%d')
    fin = sample_reserva.fecha_fin.strftime('%Y-%m-%d')
    
    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Otro Cliente',
        'email': 'otro@ejemplo.com',
        'telefono': '123456789'
    }, follow_redirects=True)
    
    assert b'no est\xc3\xa1 disponible' in response.data or b'no disponible' in response.data.lower()


def test_rate_limiting_reservas(client, sample_habitacion, db):
    inicio = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
    
    # Intentar 5 reservas
    for _ in range(5):
        response = client.post('/huespedes/habitaciones', data={
            'habitacion_id': sample_habitacion.id,
            'fecha_inicio': inicio,
            'fecha_fin': fin,
            'nombre': 'Spammer',
            'email': 'spam@ejemplo.com',
            'telefono': '123456789'
        }, follow_redirects=True)
        
    assert b'alcanzado el l\xc3\xadmite' in response.data or b'limite' in response.data.lower()


# --- 3. Procesamiento de Pagos ---

def test_pago_efectivo(client, sample_habitacion, config_hotel, db):
    # Crear reserva pendiente
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now() + timedelta(days=2),
        fecha_fin=datetime.now() + timedelta(days=4),
        codigo='EFE123',
        estado='pendiente_pago',
        email_cliente='pago@ejemplo.com'
    )
    db.session.add(res)
    db.session.commit()
    
    response = client.post(f'/huespedes/procesar_pago/{res.id}', data={
        'metodo_pago': 'efectivo'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    db.session.refresh(res)
    assert res.estado == 'activa'
    assert res.metodo_pago == 'efectivo'
    assert res.pagado == False


def test_pago_nequi(client, sample_habitacion, config_hotel, db, monkeypatch):
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now() + timedelta(days=2),
        fecha_fin=datetime.now() + timedelta(days=4),
        codigo='NEQ123',
        estado='pendiente_pago',
        email_cliente='nequi@ejemplo.com'
    )
    db.session.add(res)
    db.session.commit()
    
    data = {
        'metodo_pago': 'nequi',
        'comprobante': (BytesIO(b"fake image data"), 'comprobante.jpg')
    }
    
    response = client.post(f'/huespedes/procesar_pago/{res.id}', data=data, content_type='multipart/form-data', follow_redirects=True)
    
    assert response.status_code == 200
    db.session.refresh(res)
    assert res.estado == 'pendiente_verificacion'
    assert res.metodo_pago == 'nequi'
    assert res.comprobante_pago is not None


# --- 4. Autenticación ---

def test_registro_cliente(client, db):
    response = client.post('/huespedes/registro', data={
        'nombre': 'Nuevo Huésped',
        'email': 'nuevo@ejemplo.com',
        'telefono': '555555555',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)
    
    assert b'Registro exitoso' in response.data
    user = User.query.filter_by(email='nuevo@ejemplo.com').first()
    assert user is not None
    assert user.rol == 'cliente'


def test_login_cliente(client, cliente_user):
    response = client.post('/huespedes/login', data={
        'email': 'cliente_test@ejemplo.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert b'Bienvenido de nuevo' in response.data


# --- 5. Cancelación ---

def test_cancelar_por_codigo(client, sample_reserva, config_hotel, db):
    assert sample_reserva.estado == 'activa'
    
    response = client.post('/huespedes/cancelar_codigo', data={
        'codigo': sample_reserva.codigo
    }, follow_redirects=True)
    
    assert response.status_code == 200
    db.session.refresh(sample_reserva)
    assert sample_reserva.estado == 'cancelada'

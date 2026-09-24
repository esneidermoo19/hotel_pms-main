"""
Pruebas unitarias del módulo de Reservas.

Cubre la creación exitosa de reservas públicas y de recepción, las
validaciones de fechas y datos requeridos (HTTP 400/422 equivalentes: el
formulario se re-renderiza con 200 + mensaje de error) y el manejo de
recursos inexistentes (HTTP 404).
"""
import pytest
from datetime import datetime, timedelta

from app.models import Reservacion

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Flujo público (huéspedes)
# ---------------------------------------------------------------------------

def test_crear_reserva_publica_exitosa(client, db, sample_habitacion):
    """Creación exitosa: se persiste una reserva en estado 'pendiente_pago'."""
    inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Cliente Reserva Unitaria',
        'email': 'reserva_unitaria@ejemplo.com',
        'telefono': '3000000008',
    }, follow_redirects=True)

    assert response.status_code == 200
    reserva = Reservacion.query.filter_by(email_cliente='reserva_unitaria@ejemplo.com').first()
    assert reserva is not None
    assert reserva.estado == 'pendiente_pago'


def test_reserva_total_se_calcula_por_noches(client, db, sample_habitacion):
    """Regla de negocio: el total es (noches estancia * tarifa) y debe ser positivo."""
    inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')  # 2 noches

    client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Cliente Total',
        'email': 'total@ejemplo.com',
        'telefono': '3000000009',
    })

    reserva = Reservacion.query.filter_by(email_cliente='total@ejemplo.com').first()
    assert reserva is not None
    assert float(reserva.total_pago) > 0
    assert float(reserva.total_pago) == 2 * float(sample_habitacion.precio_noche)


def test_reserva_fecha_invalida_rechazada(client, db, sample_habitacion):
    """Validación: fecha de inicio >= fecha de fin debe rechazarse."""
    hoy = datetime.now().date()
    inicio = (hoy + timedelta(days=3)).strftime('%Y-%m-%d')
    fin = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')  # anterior al inicio

    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Cliente Fechas',
        'email': 'fechas@ejemplo.com',
        'telefono': '3000000010',
    }, follow_redirects=True)

    assert 'anterior' in response.data.decode('utf-8').lower()
    assert Reservacion.query.filter_by(email_cliente='fechas@ejemplo.com').first() is None


def test_reserva_datos_personales_obligatorios(client, db, sample_habitacion):
    """Validación: huésped anónimo debe completar nombre, email y teléfono."""
    inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': sample_habitacion.id,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': '',
        'email': 'incompleto@ejemplo.com',
        'telefono': '',
    }, follow_redirects=True)

    assert b'completar todos los datos' in response.data
    assert Reservacion.query.filter_by(email_cliente='incompleto@ejemplo.com').first() is None


def test_reserva_habitacion_inexistente_404(client, db, sample_habitacion):
    """Recurso inexistente: reservar una habitación inexistente devuelve HTTP 404."""
    inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fin = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

    response = client.post('/huespedes/habitaciones', data={
        'habitacion_id': 999999,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'nombre': 'Cliente Fantasma',
        'email': 'fantasma@ejemplo.com',
        'telefono': '3000000011',
    })

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Flujo de recepción (staff)
# ---------------------------------------------------------------------------

def _reserva_staff(payload_extra, client):
    """Auxiliar: arma el payload estándar de una reserva creada por recepción."""
    base = {
        'nombre_huesped': 'Huésped Staff Unitario',
        'telefono_huesped': '3000000012',
        'email_huesped': 'staff_unitaria@ejemplo.com',
        'cedula_nit': '123456789',
        'tipo_documento': 'cedula',
        'num_personas': '1',
        'hay_menores': 'no',
        'fecha_ingreso': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
        'fecha_salida': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
    }
    base.update(payload_extra)
    return base


def test_crear_reserva_staff_exitosa(client, db, sample_habitacion, login_staff, recepcion_user):
    """Creación exitosa de reserva por parte de recepción."""
    login_staff(recepcion_user.username, 'recep123')

    response = client.post(
        f'/staff/recepcion/reservar/{sample_habitacion.id}',
        data=_reserva_staff({}, client),
        follow_redirects=False,
    )
    assert response.status_code == 302

    reserva = Reservacion.query.filter_by(email_cliente='staff_unitaria@ejemplo.com').first()
    assert reserva is not None
    assert reserva.estado == 'activa'


def test_reserva_staff_datos_requeridos(client, db, sample_habitacion, login_staff, recepcion_user):
    """Validación en recepción: nombre, teléfono y cédula/NIT son obligatorios."""
    login_staff(recepcion_user.username, 'recep123')

    payload = _reserva_staff({'nombre_huesped': '', 'cedula_nit': ''}, client)
    response = client.post(
        f'/staff/recepcion/reservar/{sample_habitacion.id}',
        data=payload,
    )

    assert response.status_code == 302, 'Debe redirigir al formulario con el error'
    assert Reservacion.query.filter_by(email_cliente='staff_unitaria@ejemplo.com').first() is None


def test_reserva_staff_fechas_conflictivas(client, db, sample_habitacion, login_staff, recepcion_user):
    """Validación en recepción: la fecha de salida debe ser posterior a la de ingreso."""
    login_staff(recepcion_user.username, 'recep123')

    payload = _reserva_staff({
        'fecha_ingreso': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'fecha_salida': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
    }, client)

    response = client.post(
        f'/staff/recepcion/reservar/{sample_habitacion.id}',
        data=payload,
    )

    assert response.status_code == 302
    assert Reservacion.query.filter_by(email_cliente='staff_unitaria@ejemplo.com').first() is None


def test_reserva_staff_habitacion_inexistente_404(client, login_staff, recepcion_user):
    """Recurso inexistente: reservar en una habitación inexistente devuelve HTTP 404."""
    login_staff(recepcion_user.username, 'recep123')

    response = client.get('/staff/recepcion/reservar/999999')
    assert response.status_code == 404
"""
Prueba E2E del módulo de Reservas: ciclo CRUD completo e integrado.

El flujo se ejecuta desde recepción sobre una habitación real:
    1. POST   -> crear la reserva.
    2. GET    -> consultar (dashboard) y validar que figure como activa.
    3. POST   -> actualizar estado de pago (equivalente PATCH/PUT).
    4. POST   -> cancelar la reserva (equivalente DELETE; baja lógica).
    5. GET    -> confirmar que ya no exista activa (404 para recursos inexistentes).

Notas de adaptación:
- El "DELETE" del dominio hotelero es una cancelación (baja lógica, estado
  'cancelada'), por lo que se verifica la ausencia del estado activo y el
  endpoint GET sobre un recurso no existente devuelve HTTP 404.
- En testing (TESTING=True / MAIL_SUPPRESS_SEND) el correo se simula: no hay
  dependencia de SMTP real.
"""
import pytest
from datetime import datetime, timedelta

from app.models import Reservacion

pytestmark = pytest.mark.e2e


def _payload_reserva() -> dict:
    """Payload válido para crear una reserva desde recepción (fechas futuras)."""
    return {
        'nombre_huesped': 'Huésped E2E Reserva',
        'telefono_huesped': '3009998877',
        'email_huesped': 'reserva_e2e@hotel.com',
        'cedula_nit': '987654321',
        'tipo_documento': 'cedula',
        'num_personas': '2',
        'hay_menores': 'no',
        'fecha_ingreso': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
        'fecha_salida': (datetime.now() + timedelta(days=17)).strftime('%Y-%m-%d'),
    }


def test_crud_completo_reserva(client, db, sample_habitacion, login_staff, recepcion_user):
    """Flujo integrado POST -> GET -> PUT/PATCH -> DELETE -> GET final."""
    login_staff(recepcion_user.username, 'recep123')
    habitacion_id = sample_habitacion.id
    email = 'reserva_e2e@hotel.com'

    # --- PASO 1: Crear (POST) ------------------------------------------------
    response = client.post(
        f'/staff/recepcion/reservar/{habitacion_id}',
        data=_payload_reserva(),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 1: la creación exitosa debe redirigir (PRG)'

    reserva = Reservacion.query.filter_by(email_cliente=email).first()
    assert reserva is not None, 'PASO 1: la reserva debe persistirse'
    assert reserva.estado == 'activa', 'PASO 1: la reserva debe crearse activa'
    reserva_id = reserva.id
    codigo = reserva.codigo

    # --- PASO 2: Leer / Consultar (GET) --------------------------------------
    response = client.get('/staff/recepcion/dashboard')
    assert response.status_code == 200, 'PASO 2: el dashboard debe renderizarse'
    assert codigo.encode('utf-8') in response.data, 'PASO 2: la reserva debe aparecer como activa'

    # --- PASO 3: Actualizar (equivalente PATCH/PUT): registrar pago -----------
    response = client.post(
        f'/staff/recepcion/reserva/pago/{reserva_id}',
        data={'pagado': 'si'},
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 3: la actualización debe redirigir'

    reserva_actualizada = Reservacion.query.get(reserva_id)
    assert reserva_actualizada.pagado is True, 'PASO 3: el pago debe quedar marcado'
    assert reserva_actualizada.habitacion.estado == 'Ocupada', 'PASO 3: la habitación debe marcarse ocupada'

    # --- PASO 4: Eliminar (equivalente DELETE): cancelar reserva --------------
    response = client.post(
        f'/staff/recepcion/reserva/cancelar_staff/{reserva_id}',
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 4: la cancelación debe redirigir'

    reserva = Reservacion.query.get(reserva_id)
    assert reserva.estado == 'cancelada', 'PASO 4: la reserva debe quedar cancelada'

    # --- PASO 5: Confirmar (GET final) ----------------------------------------
    response = client.get('/staff/recepcion/dashboard')
    assert response.status_code == 200
    # El email del huésped es un identificador único y no debe figurar como reserva activa
    assert email.encode('utf-8') not in response.data, 'PASO 5: la reserva no debe figurar activa'

    response = client.get('/staff/recepcion/reservar/999999')
    assert response.status_code == 404, 'PASO 5: un recurso inexistente debe dar 404'
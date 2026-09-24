"""
Prueba E2E del módulo de Habitaciones: ciclo CRUD completo e integrado.

Ejecuta secuencialmente sobre la aplicación real (módulo admin, con login):
    1. POST   -> crear habitación.
    2. GET    -> consultar y validar la creación.
    3. POST   -> actualizar (equivalente PATCH/PUT) y verificar el cambio.
    4. POST   -> eliminar (equivalente DELETE).
    5. GET    -> confirmar que el recurso retorne HTTP 404 tras la eliminación.

Adaptación de códigos: la app es Flask con formularios (PRG), por lo que las
mutaciones exitosas responden 302; el estado se valida contra la base de datos
y el acceso a un recurso borrado devuelve 404 vía ``get_or_404``.
"""
import pytest

from app.models import Habitacion

pytestmark = pytest.mark.e2e


def _payload_habitacion(numero: str, tipo: str, precio: str) -> dict:
    """Payload de formulario válido para el módulo admin de habitaciones."""
    return {
        'numero': numero,
        'tipo': tipo,
        'precio_noche': precio,
        'descripcion': 'Habitación de prueba E2E',
        'cantidad_camas': '2',
        'tipo_camas': 'Full Size',
        'capacidad_max': '4',
        'wifi': 'on',
    }


def test_crud_completo_habitacion(client, db, login_staff, admin_user):
    """Flujo integrado POST -> GET -> PUT/PATCH -> DELETE -> GET(404)."""
    login_staff(admin_user.username, 'admin123')

    # --- PASO 1: Crear (POST) ------------------------------------------------
    response = client.post(
        '/staff/admin/habitaciones/nueva',
        data=_payload_habitacion('E2E-101', 'Doble Superior', '450000'),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 1: el POST exitoso debe redirigir (PRG)'

    habitacion = Habitacion.query.filter_by(numero='E2E-101').first()
    assert habitacion is not None, 'PASO 1: la habitación debe persistirse'
    habitacion_id = habitacion.id

    # --- PASO 2: Leer / Consultar (GET) --------------------------------------
    response = client.get('/staff/admin/habitaciones')
    assert response.status_code == 200, 'PASO 2: la lista debe renderizarse'
    assert b'E2E-101' in response.data, 'PASO 2: la habitación creada debe aparecer'

    # --- PASO 3: Actualizar (equivalente PATCH/PUT) ---------------------------
    response = client.post(
        f'/staff/admin/habitaciones/editar/{habitacion_id}',
        data=_payload_habitacion('E2E-101', 'Suite Orquídea', '850000'),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 3: la edición exitosa debe redirigir'

    hab_actualizada = Habitacion.query.get(habitacion_id)
    assert hab_actualizada.tipo == 'Suite Orquídea', 'PASO 3: el tipo debe actualizarse'
    assert float(hab_actualizada.precio_noche) == 850000, 'PASO 3: la tarifa debe actualizarse'

    # --- PASO 4: Eliminar (equivalente DELETE) --------------------------------
    response = client.post(
        f'/staff/admin/habitaciones/eliminar/{habitacion_id}',
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 4: la eliminación exitosa debe redirigir'
    assert Habitacion.query.get(habitacion_id) is None, 'PASO 4: la fila debe desaparecer'

    # --- PASO 5: Confirmar eliminación (GET final -> HTTP 404) ----------------
    response = client.get(f'/staff/admin/habitaciones/editar/{habitacion_id}')
    assert response.status_code == 404, 'PASO 5: editar un recurso borrado debe dar 404'

    response = client.get('/staff/admin/habitaciones')
    assert response.status_code == 200
    assert b'E2E-101' not in response.data, 'PASO 5: la habitación no debe listarse'
"""
Prueba E2E del módulo de Clientes/Huéspedes: ciclo CRUD completo e integrado.

Al no existir una entidad ``Cliente`` separada, el flujo se ejecuta sobre el
modelo ``User`` con rol ``cliente`` gestionado desde administración:
    1. POST   -> crear cliente (rol 'cliente').
    2. GET    -> consultar y validar la creación.
    3. POST   -> actualizar (equivalente PATCH/PUT) y verificar el cambio.
    4. POST   -> eliminar (equivalente DELETE).
    5. GET    -> confirmar que el recurso retorne HTTP 404 tras la eliminación.

Adaptación de códigos: como es una app Flask con formularios, las mutaciones
exitosas redirigen (302); el estado se verifica en base de datos y el acceso a
un usuario borrado devuelve 404 vía ``get_or_404``.
"""
import pytest

from app.models import User

pytestmark = pytest.mark.e2e


def _payload_usuario(username: str, nombre: str, email: str) -> dict:
    """Payload de formulario válido para el alta de usuarios (rol cliente)."""
    return {
        'username': username,
        'password': 'clave_e2e_123',
        'nombre': nombre,
        'email': email,
        'telefono': '3005556677',
        'rol': 'cliente',
    }


def test_crud_completo_cliente(client, db, login_staff, admin_user):
    """Flujo integrado POST -> GET -> PUT/PATCH -> DELETE -> GET(404)."""
    login_staff(admin_user.username, 'admin123')

    username = 'cliente_e2e'
    email = 'cliente_e2e@hotel.com'

    # --- PASO 1: Crear (POST) ------------------------------------------------
    response = client.post(
        '/staff/admin/usuarios/nuevo',
        data=_payload_usuario(username, 'Cliente E2E', email),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 1: el alta exitosa debe redirigir (PRG)'

    cliente = User.query.filter_by(username=username).first()
    assert cliente is not None, 'PASO 1: el cliente debe persistirse'
    assert cliente.rol == 'cliente', 'PASO 1: el rol debe ser cliente'
    cliente_id = cliente.id

    # --- PASO 2: Leer / Consultar (GET) --------------------------------------
    response = client.get('/staff/admin/usuarios')
    assert response.status_code == 200, 'PASO 2: la lista de usuarios debe renderizarse'
    assert username.encode('utf-8') in response.data, 'PASO 2: el cliente debe aparecer en la lista'

    # --- PASO 3: Actualizar (equivalente PATCH/PUT) ---------------------------
    response = client.post(
        f'/staff/admin/usuarios/editar/{cliente_id}',
        data=_payload_usuario(username, 'Cliente E2E Editado', email),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 3: la edición exitosa debe redirigir'

    cliente_actualizado = User.query.get(cliente_id)
    assert cliente_actualizado.nombre == 'Cliente E2E Editado', 'PASO 3: el nombre debe actualizarse'

    # --- PASO 4: Eliminar (equivalente DELETE) --------------------------------
    response = client.post(
        f'/staff/admin/usuarios/eliminar/{cliente_id}',
        follow_redirects=False,
    )
    assert response.status_code == 302, 'PASO 4: la eliminación exitosa debe redirigir'
    assert User.query.get(cliente_id) is None, 'PASO 4: la fila debe desaparecer'

    # --- PASO 5: Confirmar eliminación (GET final -> HTTP 404) ----------------
    response = client.get(f'/staff/admin/usuarios/editar/{cliente_id}')
    assert response.status_code == 404, 'PASO 5: editar un recurso borrado debe dar 404'

    response = client.get('/staff/admin/usuarios')
    assert response.status_code == 200
    assert username.encode('utf-8') not in response.data, 'PASO 5: el cliente no debe listarse'
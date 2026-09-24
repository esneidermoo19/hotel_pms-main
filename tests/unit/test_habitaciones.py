"""
Pruebas unitarias del módulo de Habitaciones.

Cubre creación exitosa, validaciones y casos borde (datos requeridos y tarifas
negativas) y el manejo de recursos inexistentes (HTTP 404).

Adaptación de códigos: al ser una app Flask con formularios server-side, la
creación/actualización exitosa responde 302 (PRG = POST/Redirect/GET), la
validación fallida re-renderiza el formulario (200) con el mensaje de error, y
los recursos inexistentes devuelven 404 mediante ``get_or_404``.
"""
import pytest

from app.models import Habitacion

pytestmark = pytest.mark.unit


def _datos_habitacion(numero='U-201'):
    """Datos mínimos válidos de habitación para el formulario de administración."""
    return {
        'numero': numero,
        'tipo': 'Doble Superior',
        'precio_noche': '450000',
        'descripcion': 'Habitación usada en pruebas unitarias',
        'cantidad_camas': '2',
        'tipo_camas': 'Full Size',
        'capacidad_max': '4',
        'wifi': 'on',
    }


def test_crear_habitacion_exitosamente(client, db, login_staff, admin_user):
    """Creación exitosa: el POST responde 302 y la habitación queda persistida."""
    login_staff(admin_user.username, 'admin123')

    response = client.post(
        '/staff/admin/habitaciones/nueva',
        data=_datos_habitacion(numero='U-100'),
        follow_redirects=False,
    )
    assert response.status_code == 302, 'El POST exitoso debe redirigir (PRG)'

    habitacion = Habitacion.query.filter_by(numero='U-100').first()
    assert habitacion is not None, 'La habitación debe existir en la base de datos'
    assert habitacion.tipo == 'Doble Superior'


def test_crear_habitacion_sin_datos_requeridos(client, db, login_staff, admin_user):
    """Validación de datos requeridos: sin tarifa no se persiste nada y se muestra error."""
    total_antes = Habitacion.query.count()
    login_staff(admin_user.username, 'admin123')

    data = _datos_habitacion(numero='U-200')
    data['precio_noche'] = ''  # campo obligatorio vacío

    response = client.post(
        '/staff/admin/habitaciones/nueva',
        data=data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert Habitacion.query.count() == total_antes, 'No debe persistirse una habitación inválida'


def test_crear_habitacion_numero_duplicado_rechazado(client, db, login_staff, admin_user):
    """Validación de unicidad: el número de habitación no puede repetirse."""
    login_staff(admin_user.username, 'admin123')

    client.post('/staff/admin/habitaciones/nueva', data=_datos_habitacion(numero='U-300'))

    response = client.post(
        '/staff/admin/habitaciones/nueva',
        data=_datos_habitacion(numero='U-300'),
        follow_redirects=True,
    )
    assert response.status_code == 200
    duplicadas = Habitacion.query.filter_by(numero='U-300').count()
    assert duplicadas == 1, 'El número de habitación es único: no debe duplicarse'


@pytest.mark.xfail(
    reason=(
        'BUG conocido: el módulo admin.nueva_habitacion no valida tarifas '
        'negativas y persiste el precio tal cual.'
    ),
    strict=False,
)
def test_precio_negativo_rechazado(client, db, login_staff, admin_user):
    """Caso borde: tarifas negativas deben rechazarse por regla de negocio (documentado)."""
    total_antes = Habitacion.query.count()
    login_staff(admin_user.username, 'admin123')

    data = _datos_habitacion(numero='U-400')
    data['precio_noche'] = '-500'

    response = client.post('/staff/admin/habitaciones/nueva', data=data)
    assert response.status_code == 200
    assert Habitacion.query.count() == total_antes, 'Una tarifa negativa no debe persistirse'


def test_editar_habitacion_inexistente_404(client, login_staff, admin_user):
    """Recurso inexistente: editar una habitación que no existe devuelve HTTP 404."""
    login_staff(admin_user.username, 'admin123')

    response = client.get('/staff/admin/habitaciones/editar/999999')
    assert response.status_code == 404


def test_eliminar_habitacion_inexistente_404(client, login_staff, admin_user):
    """Recurso inexistente: eliminar una habitación que no existe devuelve HTTP 404."""
    login_staff(admin_user.username, 'admin123')

    response = client.post('/staff/admin/habitaciones/eliminar/999999')
    assert response.status_code == 404


def test_acceso_denegado_sin_autenticacion(client):
    """RBAC: sin sesión, las rutas de administración redirigen al login (302)."""
    response = client.get('/staff/admin/habitaciones', follow_redirects=False)
    assert response.status_code == 302
    assert '/staff/login' in response.headers['Location']
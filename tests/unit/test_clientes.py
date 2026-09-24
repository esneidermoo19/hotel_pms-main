"""
Pruebas unitarias del módulo de Clientes / Huéspedes.

Cubre el registro público de huéspedes, la gestión de clientes por parte de
administración (modelo ``User`` con rol ``cliente``) y el alta de clientes de
facturación (modelo ``ClienteFactura``), incluyendo validaciones de unicidad y
recursos inexistentes (HTTP 404).

Nota: la aplicación no expone una entidad ``Cliente`` separada; el huésped se
representa con el modelo ``User`` (rol ``cliente``) y con ``ClienteFactura``
para la facturación.
"""
import pytest

from app.models import User, ClienteFactura

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Registro público de huéspedes (módulo cliente)
# ---------------------------------------------------------------------------

def test_registro_cliente_publico_exitoso(client, db):
    """Registro público exitoso: se crea un usuario con rol 'cliente'."""
    response = client.post('/huespedes/registro', data={
        'nombre': 'Huésped Unitario',
        'email': 'unitaria@ejemplo.com',
        'telefono': '3000000001',
        'password': 'secreto123',
        'password_confirm': 'secreto123',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registro exitoso' in response.data
    usuario = User.query.filter_by(email='unitaria@ejemplo.com').first()
    assert usuario is not None
    assert usuario.rol == 'cliente'


def test_registro_cliente_email_duplicado_rechazado(client, db):
    """Validación: un correo ya registrado en la BD no puede crearse nuevamente."""
    existente = User(
        username='repetido@ejemplo.com',
        email='repetido@ejemplo.com',
        nombre='Huésped Existente',
        rol='cliente',
        activo=True,
    )
    existente.password = 'secreto123'
    db.session.add(existente)
    db.session.commit()

    response = client.post('/huespedes/registro', data={
        'nombre': 'Segundo Huésped',
        'email': 'repetido@ejemplo.com',
        'telefono': '3000000003',
        'password': 'secreto123',
        'password_confirm': 'secreto123',
    }, follow_redirects=True)

    assert b'ya est\xc3\xa1 registrado' in response.data or b'ya esta registrado' in response.data
    assert User.query.filter_by(email='repetido@ejemplo.com').count() == 1


def test_registro_cliente_contraseñas_no_coinciden(client, db):
    """Validación: contraseñas distintas deben rechazarse sin crear el usuario."""
    response = client.post('/huespedes/registro', data={
        'nombre': 'Huésped Contraseña',
        'email': 'claves@ejemplo.com',
        'telefono': '3000000004',
        'password': 'secreto123',
        'password_confirm': 'otra123',
    }, follow_redirects=True)

    assert b'coinciden' in response.data
    assert User.query.filter_by(email='claves@ejemplo.com').first() is None


# ---------------------------------------------------------------------------
# Gestión de clientes desde administración (User con rol 'cliente')
# ---------------------------------------------------------------------------

def test_crear_cliente_por_admin(client, db, login_staff, admin_user):
    """Creación exitosa de un cliente desde el panel de administración."""
    login_staff(admin_user.username, 'admin123')

    response = client.post('/staff/admin/usuarios/nuevo', data={
        'username': 'cliente_adm',
        'password': 'clave123',
        'nombre': 'Cliente Administrado',
        'email': 'cliente_adm@hotel.com',
        'telefono': '3000000005',
        'rol': 'cliente',
    }, follow_redirects=False)

    assert response.status_code == 302, 'El alta exitosa debe redirigir a la lista'
    usuario = User.query.filter_by(username='cliente_adm').first()
    assert usuario is not None
    assert usuario.rol == 'cliente'


def test_crear_cliente_username_duplicado_rechazado(client, db, login_staff, admin_user):
    """Validación de unicidad: el username no puede repetirse en el sistema."""
    login_staff(admin_user.username, 'admin123')

    datos = {
        'username': 'cliente_dup',
        'password': 'clave123',
        'nombre': 'Cliente Duplicado',
        'email': 'cliente_dup@hotel.com',
        'telefono': '3000000006',
        'rol': 'cliente',
    }
    client.post('/staff/admin/usuarios/nuevo', data=datos)

    response = client.post('/staff/admin/usuarios/nuevo', data=datos,
                           follow_redirects=True)
    assert b'ya existe' in response.data
    assert User.query.filter_by(username='cliente_dup').count() == 1


def test_editar_usuario_inexistente_404(client, login_staff, admin_user):
    """Recurso inexistente: editar un usuario que no existe devuelve HTTP 404."""
    login_staff(admin_user.username, 'admin123')

    response = client.get('/staff/admin/usuarios/editar/999999')
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Clientes de facturación (modelo ClienteFactura)
# ---------------------------------------------------------------------------

def test_crear_cliente_facturacion_exitoso(client, db, login_staff, admin_user):
    """Alta exitosa de un cliente de facturación con NIT y nombre."""
    login_staff(admin_user.username, 'admin123')

    response = client.post('/staff/empleado/cliente/nuevo', data={
        'nit': '901234567-1',
        'nombre': 'Empresa Test S.A.S.',
        'tipo_documento': 'nit',
        'direccion': 'Calle 10 # 20-30',
        'email': 'factura@test.com',
        'telefono': '3000000007',
    }, follow_redirects=False)

    assert response.status_code == 302
    cliente = ClienteFactura.query.filter_by(nit='901234567-1').first()
    assert cliente is not None
    assert cliente.nombre == 'Empresa Test S.A.S.'


def test_cliente_facturacion_nit_duplicado_rechazado(client, db, login_staff, admin_user):
    """Validación de unicidad: un NIT ya existente no puede repetirse."""
    login_staff(admin_user.username, 'admin123')

    datos = {
        'nit': '901234567-2',
        'nombre': 'Empresa A',
        'tipo_documento': 'nit',
    }
    client.post('/staff/empleado/cliente/nuevo', data=datos)

    datos['nombre'] = 'Empresa B'
    response = client.post('/staff/empleado/cliente/nuevo', data=datos,
                           follow_redirects=True)

    assert b'Ya existe un cliente con este NIT' in response.data
    assert ClienteFactura.query.filter_by(nit='901234567-2').count() == 1


def test_cliente_facturacion_sin_nit_rechazado(client, db, login_staff, admin_user):
    """Validación de datos requeridos: NIT y nombre son obligatorios."""
    login_staff(admin_user.username, 'admin123')

    response = client.post('/staff/empleado/cliente/nuevo', data={
        'nit': '',
        'nombre': '',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'NIT y Nombre son obligatorios' in response.data
"""
Pruebas de UI del módulo de clientes/huéspedes (Playwright).

Flujos cubiertos:
- Registro público en /huespedes/registro: tras crear la cuenta el cliente
  queda autenticado y es redirigido a /huespedes/mis_reservas.
- Validación de contraseñas distintas: flash de error sin abandonar el form.
- Cliente registrado NO puede acceder al portal staff (acceso denegado).
- Admin puede crear y editar un usuario de personal desde /staff/admin/usuarios.
"""
import re
import time

import pytest
from playwright.sync_api import expect


def _email_unico(prefix='ui.cliente'):
    return f'{prefix}+{int(time.time() * 1000)}@test.com'


@pytest.mark.ui
def test_registro_cliente_publico_redirige_a_mis_reservas(page, base_url):
    page.goto(f'{base_url}/huespedes/registro')

    page.fill('#nombre', 'Cliente UI Test')
    page.fill('#email', _email_unico())
    page.fill('#telefono', '+57 300 000 0000')
    page.fill('#password', 'clave123')
    page.fill('#password_confirm', 'clave123')
    page.click('button.auth-btn')

    expect(page).to_have_url(base_url + '/huespedes/mis_reservas')
    expect(page.get_by_text('Registro exitoso. ¡Bienvenido!')).to_be_visible()


@pytest.mark.ui
def test_registro_cliente_contrasenas_distintas_muestran_error(page, base_url):
    page.goto(f'{base_url}/huespedes/registro')

    page.fill('#nombre', 'Cliente Coincidencia')
    page.fill('#email', _email_unico('ui.coincidencia'))
    page.fill('#telefono', '+57 300 000 0001')
    page.fill('#password', 'clave123')
    page.fill('#password_confirm', 'otra_clave')
    page.click('button.auth-btn')

    expect(page).to_have_url(base_url + '/huespedes/registro')
    expect(page.get_by_text('Las contraseñas no coinciden.')).to_be_visible()


@pytest.mark.ui
def test_cliente_no_accede_al_panel_staff(page, base_url):
    # Registrar un cliente y después intentar el ingreso al portal staff.
    email = _email_unico('ui.bloqueado')
    page.goto(f'{base_url}/huespedes/registro')
    page.fill('#nombre', 'Cliente Bloqueado')
    page.fill('#email', email)
    page.fill('#telefono', '+57 300 000 0002')
    page.fill('#password', 'clave123')
    page.fill('#password_confirm', 'clave123')
    page.click('button.auth-btn')
    expect(page).to_have_url(base_url + '/huespedes/mis_reservas')

    page.goto(f'{base_url}/staff/login')
    page.fill('#username', email)
    page.fill('#password', 'clave123')
    page.click('#login-button')

    expect(page).to_have_url(base_url + '/staff/login')
    expect(page.get_by_text(
        'Acceso denegado. Este portal es exclusivo para el personal.'
    )).to_be_visible()


@pytest.mark.ui
def test_admin_crea_y_edita_usuario(page, ui_login, base_url):
    usuario = f'ui_operario_{int(time.time() * 1000)}'
    ui_login('admin_ui', 'ui_test_123')

    # Crear usuario de personal.
    page.goto(f'{base_url}/staff/admin/usuarios/nuevo')
    page.fill('#username', usuario)
    page.fill('#nombre', 'Operario UI Test')
    page.select_option('#rol', 'recepcionista')
    page.fill('#password', 'op12345')
    page.click('button[type="submit"]')

    expect(page).to_have_url(base_url + '/staff/admin/usuarios')
    fila = page.locator('table tbody tr').filter(has_text=usuario)
    expect(fila).to_be_visible()
    expect(fila.get_by_text('Operario UI Test')).to_be_visible()

    # Editar el usuario creado.
    fila.locator('a[title="Editar"]').click()
    expect(page).to_have_url(
        re.compile(re.escape(base_url) + r'/staff/admin/usuarios/editar/\d+')
    )

    page.fill('#nombre', 'Operario UI Renombrado')
    page.click('button[type="submit"]')

    expect(page).to_have_url(base_url + '/staff/admin/usuarios')
    fila_editada = page.locator('table tbody tr').filter(has_text=usuario)
    expect(fila_editada.get_by_text('Operario UI Renombrado')).to_be_visible()
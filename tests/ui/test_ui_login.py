"""
Pruebas de UI del inicio de sesión del panel staff (Playwright).

Flujos cubiertos:
- Login exitoso como administrador (redirige a /staff/admin/).
- Login exitoso como recepcionista (redirige a /staff/recepcion/).
- Credenciales inválidas: permanece en el formulario con flash de error.
- Acceso a página protegida sin sesión: redirige a /staff/login y, al
  autenticarse, lleva al destino.

Usuarios semilla creados por tests/ui/server.py:
    admin_ui / ui_test_123  (rol admin)
    recep_ui / recep_ui_123 (rol recepcionista)
"""
import pytest
from playwright.sync_api import expect


@pytest.mark.ui
def test_login_admin_redirige_al_dashboard(page, ui_login, base_url):
    ui_login('admin_ui', 'ui_test_123')

    expect(page).to_have_url(base_url + '/staff/admin/')
    expect(page.get_by_text('¡Bienvenido!')).to_be_visible()


@pytest.mark.ui
def test_login_recepcion_redirige_al_panel(page, ui_login, base_url):
    page.goto(f'{base_url}/staff/login')
    page.locator('.role-tab', has_text='Recepción').click()
    page.fill('#username', 'recep_ui')
    page.fill('#password', 'recep_ui_123')
    page.click('#login-button')

    expect(page).to_have_url(base_url + '/staff/recepcion/dashboard')
    expect(page.get_by_text('¡Bienvenido!')).to_be_visible()


@pytest.mark.ui
def test_login_credenciales_invalidas_muestran_error(page, base_url):
    page.goto(f'{base_url}/staff/login')
    page.fill('#username', 'admin_ui')
    page.fill('#password', 'clave_incorrecta')
    page.click('#login-button')

    expect(page).to_have_url(base_url + '/staff/login')
    expect(page.locator('.flash-message.danger')).to_contain_text(
        'Usuario o contraseña incorrectos.')


@pytest.mark.ui
def test_pagina_protegida_redirige_al_login_y_luego_entra(page, base_url, ui_login):
    page.goto(f'{base_url}/staff/admin/habitaciones')

    expect(page).to_have_url(base_url + '/staff/login')
    expect(page.locator('.flash-message.warning')).to_contain_text(
        'Por favor inicie sesión')

    ui_login('admin_ui', 'ui_test_123')
    expect(page).to_have_url(base_url + '/staff/admin/')
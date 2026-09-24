"""
Pruebas de UI de la gestión de habitaciones (módulo admin, Playwright).

Flujos CRUD completos contra el navegador real:
- Crear una habitación vía /staff/admin/habitaciones/nueva y verificar que sus
  datos aparecen renderizados en el listado.
- Validación HTML5 del formulario (campos obligatorios vacíos no envían).
- Editar una habitación existente y verificar los valores actualizados.
- Eliminar una habitación confirmando el diálogo nativo de confirm().

Nota de adaptación: la vista de listado de habitaciones es una GRID de
tarjetas (.elegant-card → .grid-rooms), no una tabla HTML. Por eso las
aserciones inspeccionan la tarjeta correspondiente en lugar de un <tr>.
"""
import re

import pytest
from playwright.sync_api import expect


@pytest.mark.ui
def test_crear_habitacion_aparece_en_listado(page, ui_login, base_url):
    ui_login('admin_ui', 'ui_test_123')

    page.goto(f'{base_url}/staff/admin/habitaciones/nueva')
    page.fill('#numero', 'UI-101')
    page.select_option('#tipo', 'Suite')
    page.fill('#precio_noche', '1250000')
    page.fill('#capacidad_max', '2')
    page.fill('#cantidad_camas', '1')
    page.select_option('#tipo_camas', 'King')
    page.click('button[type="submit"]')

    expect(page).to_have_url(base_url + '/staff/admin/habitaciones')

    tarjeta = page.locator('.elegant-card').filter(has_text='Habitación UI-101')
    expect(tarjeta).to_be_visible()
    expect(tarjeta.get_by_text('Suite')).to_be_visible()
    expect(tarjeta.get_by_text('$1,250,000')).to_be_visible()


@pytest.mark.ui
def test_crear_habitacion_validacion_campos_requeridos(page, ui_login, base_url):
    ui_login('admin_ui', 'ui_test_123')

    page.goto(f'{base_url}/staff/admin/habitaciones/nueva')
    page.click('button[type="submit"]')

    # Sin navegación: el navegador bloquea el envío por HTML5 (campos requeridos).
    expect(page).to_have_url(base_url + '/staff/admin/habitaciones/nueva')


@pytest.mark.ui
def test_editar_habitacion_actualiza_datos(page, ui_login, base_url):
    ui_login('admin_ui', 'ui_test_123')

    page.goto(f'{base_url}/staff/admin/habitaciones')
    tarjeta = page.locator('.elegant-card').filter(has_text='Habitación 101')
    expect(tarjeta).to_be_visible()

    tarjeta.locator('a[title="Editar"]').click()
    expect(page).to_have_url(
        re.compile(re.escape(base_url) + r'/staff/admin/habitaciones/editar/\d+')
    )

    page.fill('#precio_noche', '295000')
    page.select_option('#tipo', 'Junior Suite')
    page.click('button[type="submit"]')

    expect(page).to_have_url(base_url + '/staff/admin/habitaciones')
    tarjeta_editada = page.locator('.elegant-card').filter(has_text='Habitación 101')
    expect(tarjeta_editada.get_by_text('Junior Suite')).to_be_visible()
    expect(tarjeta_editada.get_by_text('$295,000')).to_be_visible()


@pytest.mark.ui
def test_eliminar_habitacion_confirmando_dialogo(page, ui_login, base_url):
    ui_login('admin_ui', 'ui_test_123')

    # Crear una habitación desechable para no tocar los datos de ejemplo.
    page.goto(f'{base_url}/staff/admin/habitaciones/nueva')
    page.fill('#numero', 'UI-999')
    page.select_option('#tipo', 'Doble')
    page.fill('#precio_noche', '500000')
    page.click('button[type="submit"]')
    expect(page).to_have_url(base_url + '/staff/admin/habitaciones')

    tarjeta = page.locator('.elegant-card').filter(has_text='Habitación UI-999')
    expect(tarjeta).to_be_visible()

    page.once('dialog', lambda dialog: dialog.accept())
    tarjeta.locator('button[title="Eliminar"]').click()

    expect(tarjeta).to_be_hidden()
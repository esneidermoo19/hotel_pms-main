import pytest

from app.models import Empleado


pytestmark = pytest.mark.unit


def test_documento_identidad_se_escribe_en_ambas_columnas():
    empleado = Empleado(nombre='Empleado de prueba', documento_identidad='CC-123')

    assert empleado.documento_identidad == 'CC-123'
    assert empleado.documento_identidad_v2 == 'CC-123'

    empleado.documento_identidad = 'CC-456'

    assert empleado.documento_identidad_v2 == 'CC-456'
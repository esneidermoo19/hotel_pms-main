from datetime import datetime

def formatear_moneda(valor):
    """Formatea un número como moneda COP"""
    if valor is None:
        return "$0"
    try:
        return "${:,.0f}".format(float(valor)).replace(',', '.')
    except (ValueError, TypeError):
        return str(valor)

def formatear_fecha(fecha, formato='%d/%m/%Y'):
    """Formatea un objeto datetime a string"""
    if not fecha:
        return ""
    if isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            return fecha
    return fecha.strftime(formato)

def currency_filter(value):
    try:
        return "{:,.0f}".format(float(value)).replace(',', '.')
    except (ValueError, TypeError):
        return value

def hora_12h(fecha):
    if not fecha:
        return '—'
    h = fecha.hour
    m = fecha.minute
    ampm = 'AM'
    if h >= 12:
        ampm = 'PM'
        if h > 12:
            h -= 12
    elif h == 0:
        h = 12
    return f"{h}:{m:02d} {ampm}"

def register_filters(app):
    app.template_filter('currency')(currency_filter)
    app.template_filter('hora12')(hora_12h)

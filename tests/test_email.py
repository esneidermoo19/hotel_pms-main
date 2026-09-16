"""Verifica que al crear/confirmar una reserva se intenta enviar el correo (mockeado)."""
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import patch
from app.models import Reservacion, ConfigHotel
from app.services.email_service import EmailService
from app import db


def _config(db):
    c = ConfigHotel(nombre='Hotel Test', nit='123', email='test@hotel.com',
                    nequi_numero='300 123 4567')
    db.session.add(c)
    db.session.commit()
    return c


def test_enviar_confirmacion_intenta_correo(app, db, sample_habitacion):
    _config(db)
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now() + timedelta(days=1),
        fecha_fin=datetime.now() + timedelta(days=3),
        codigo='ABC123', estado='activa', nombre_cliente='Ana',
        email_cliente='ana@ejemplo.com', total_pago=300000,
        metodo_pago='efectivo',
    )
    db.session.add(res)
    db.session.commit()
    with app.app_context():
        with patch.object(EmailService, 'enviar_correo', return_value=True) as mock:
            ok = EmailService.enviar_confirmacion_reserva(res, sample_habitacion, ConfigHotel.query.first())
            assert ok is True
            mock.assert_called_once()
            args, kwargs = mock.call_args
            html = kwargs.get('html_body', '') if kwargs else ''
            for dato in ['Ana', 'ABC123', '2', 'efectivo', '300']:
                assert dato.lower() in html.lower()


def test_plantilla_nequi_indica_pendiente(app, db, sample_habitacion):
    _config(db)
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now() + timedelta(days=1),
        fecha_fin=datetime.now() + timedelta(days=3),
        codigo='NEQ999', estado='pendiente_verificacion', nombre_cliente='Luis',
        email_cliente='luis@ejemplo.com', total_pago=300000, metodo_pago='nequi',
    )
    db.session.add(res)
    db.session.commit()
    with app.app_context():
        with patch.object(EmailService, 'enviar_correo', return_value=True) as mock:
            EmailService.enviar_confirmacion_reserva(res, sample_habitacion, ConfigHotel.query.first())
            html = mock.call_args[1]['html_body'] if mock.call_args[1] else ''
            assert 'pendiente de verificaci' in html.lower()
            assert 'nequi' in html.lower()


def test_fallo_correo_no_rompe_reserva(client, sample_habitacion, db):
    c = _config(db)
    res = Reservacion(
        habitacion_id=sample_habitacion.id,
        fecha_inicio=datetime.now() + timedelta(days=2),
        fecha_fin=datetime.now() + timedelta(days=4),
        codigo='FAL001', estado='pendiente_pago', email_cliente='f@ejemplo.com',
        nombre_cliente='Falla', total_pago=150000,
    )
    db.session.add(res)
    db.session.commit()
    with patch.object(EmailService, 'enviar_correo', return_value=False):
        resp = client.post(f'/huespedes/procesar_pago/{res.id}',
                           data={'metodo_pago': 'efectivo'}, follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(res)
        # La reserva se guarda igual...
        assert res.estado == 'activa'
        # ...pero queda visible el fallo para reintento manual
        assert res.email_estado == 'fallido'
        assert res.email_intentos >= 1


def test_flujos_efectivo_nequi_staff_intentan_correo(client, app, db, sample_habitacion,
                                                    recepcion_user):
    _config(db)
    # 1. Efectivo
    r1 = Reservacion(habitacion_id=sample_habitacion.id,
                     fecha_inicio=datetime.now() + timedelta(days=2),
                     fecha_fin=datetime.now() + timedelta(days=4),
                     codigo='EF0001', estado='pendiente_pago',
                     email_cliente='e@ejemplo.com', nombre_cliente='E',
                     total_pago=150000)
    db.session.add(r1)
    db.session.commit()
    with patch.object(EmailService, 'enviar_correo', return_value=True) as m1:
        client.post(f'/huespedes/procesar_pago/{r1.id}',
                    data={'metodo_pago': 'efectivo'}, follow_redirects=True)
        assert m1.called

    # 2. Nequi
    r2 = Reservacion(habitacion_id=sample_habitacion.id,
                     fecha_inicio=datetime.now() + timedelta(days=6),
                     fecha_fin=datetime.now() + timedelta(days=8),
                     codigo='NQ0002', estado='pendiente_pago',
                     email_cliente='n@ejemplo.com', nombre_cliente='N',
                     total_pago=150000)
    db.session.add(r2)
    db.session.commit()
    with patch.object(EmailService, 'enviar_correo', return_value=True) as m2:
        client.post(f'/huespedes/procesar_pago/{r2.id}', data={
            'metodo_pago': 'nequi',
            'comprobante': (BytesIO(b"fake"), 'c.jpg'),
        }, content_type='multipart/form-data', follow_redirects=True)
        assert m2.called

    # 3. Staff (recepción) — login y reserva directa
    client.post('/staff/login', data={'username': 'recep_test',
                                      'password': 'recep123'},
                follow_redirects=True)
    from datetime import date
    fi = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    fo = (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d')
    with patch.object(EmailService, 'enviar_correo', return_value=True) as m3:
        client.post(f'/staff/recepcion/reservar/{sample_habitacion.id}', data={
            'nombre_huesped': 'Staff Guest', 'telefono_huesped': '3001112222',
            'email_huesped': 'staff@ejemplo.com', 'cedula_nit': '123',
            'tipo_documento': 'cedula', 'num_personas': '1',
            'fecha_ingreso': fi, 'fecha_salida': fo,
        }, follow_redirects=True)
        assert m3.called

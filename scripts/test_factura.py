from app import create_app, db
from app.models import Reservacion
from flask import url_for

app = create_app()
with app.app_context():
    r = Reservacion.query.filter_by(estado='activa').first()
    if r:
        print(f"Reserva encontrada: {r.id}")
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1 # Assuming user 1 is admin
                sess['_user_id'] = '1'
            resp = c.post(f'/empleado/cobrar/{r.id}', data={'factura_electronica': 'si', 'csrf_token': ''})
            print(resp.status_code)
            print(resp.headers.get('Location'))
            if resp.status_code >= 400:
                print(resp.data.decode('utf-8'))
    else:
        print("No activa reservas")

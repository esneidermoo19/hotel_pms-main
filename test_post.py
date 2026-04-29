from app import create_app, db
from app.models import Reservacion
app = create_app()
with app.app_context():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['_user_id'] = '1'
        r = Reservacion.query.first()
        if r:
            resp = c.post(f'/empleado/cobrar/{r.id}', data={'factura_electronica': 'si'})
            print("Status Code:", resp.status_code)
            print("Location:", resp.headers.get('Location'))
            if resp.status_code >= 400:
                print("Error Data:", resp.data)
        else:
            print("No reservations to test.")

import unittest
import os

# Forzar base de datos en memoria para pruebas
os.environ['DATABASE_URL'] = ''

from app import create_app, db
from app.models import User

class StaffAuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Crear usuario Admin de prueba
            self.admin = User(username='admin_test', password='adminpassword123', nombre='Admin Test', rol='admin')
            # Crear usuario Recepcionista de prueba
            self.recep = User(username='recep_test', password='receppassword123', nombre='Recep Test', rol='recepcionista')
            
            db.session.add(self.admin)
            db.session.add(self.recep)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_admin_redirect(self):
        """Prueba login correcto de admin y redireccion a /staff/admin"""
        response = self.client.post('/staff/login', data={
            'username': 'admin_test',
            'password': 'adminpassword123'
        }, follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/staff/admin', response.location)

    def test_login_recep_redirect(self):
        """Prueba login correcto de recepcionista y redireccion a /staff/recepcion"""
        response = self.client.post('/staff/login', data={
            'username': 'recep_test',
            'password': 'receppassword123'
        }, follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/staff/recepcion', response.location)

    def test_unauthenticated_staff_redirect(self):
        """Prueba que un usuario sin sesion en /staff/* sea redirigido a /staff/login"""
        # Usar rutas que realmente existen: /staff/admin/ y /staff/recepcion/dashboard
        response = self.client.get('/staff/admin/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/staff/login', response.location)

        response_recep = self.client.get('/staff/recepcion/dashboard', follow_redirects=False)
        self.assertEqual(response_recep.status_code, 302)
        self.assertIn('/staff/login', response_recep.location)

    def test_recep_denied_admin_access(self):
        """Prueba que recepcionista tenga acceso denegado a rutas de admin"""
        # Iniciar sesion como recepcionista
        self.client.post('/staff/login', data={
            'username': 'recep_test',
            'password': 'receppassword123'
        })
        
        # Intentar acceder a dashboard de admin (/staff/admin/)
        response = self.client.get('/staff/admin/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        # Debe redirigir fuera de admin (a recepcion o login)
        self.assertNotIn('/staff/admin/', response.location)

    def test_old_pin_route_404(self):
        """Prueba que la ruta vieja del PIN (/verificar-staff) ya no exista y retorne 404"""
        response = self.client.post('/verificar-staff', json={'pin': '9040'})
        self.assertEqual(response.status_code, 404)

    def test_login_page_accessible(self):
        """Prueba que /staff/login sea accesible sin autenticacion"""
        response = self.client.get('/staff/login')
        self.assertEqual(response.status_code, 200)

    def test_wrong_password_rejected(self):
        """Prueba que credenciales incorrectas sean rechazadas"""
        response = self.client.post('/staff/login', data={
            'username': 'admin_test',
            'password': 'wrong_password'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'incorrectos', response.data)

if __name__ == '__main__':
    unittest.main()

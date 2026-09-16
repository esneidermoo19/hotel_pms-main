import pytest
from app.helpers.security import SecurityManager

def test_login_admin_redirect(client, admin_user):
    """Prueba login correcto de admin y redirección a /staff/admin."""
    response = client.post('/staff/login', data={
        'username': admin_user.username,
        'password': 'admin123'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/staff/admin' in response.headers['Location']

def test_login_recep_redirect(client, recepcion_user):
    """Prueba login correcto de recepcionista y redirección a /staff/recepcion."""
    response = client.post('/staff/login', data={
        'username': recepcion_user.username,
        'password': 'recep123'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/staff/recepcion' in response.headers['Location']

def test_unauthenticated_staff_redirect(client):
    """Prueba que un usuario sin sesión en /staff/* sea redirigido a /staff/login."""
    response_admin = client.get('/staff/admin/', follow_redirects=False)
    assert response_admin.status_code == 302
    assert '/staff/login' in response_admin.headers['Location']

    response_recep = client.get('/staff/recepcion/dashboard', follow_redirects=False)
    assert response_recep.status_code == 302
    assert '/staff/login' in response_recep.headers['Location']

def test_recep_denied_admin_access(client, recepcion_user):
    """Prueba que recepcionista tenga acceso denegado a rutas de admin."""
    # Iniciar sesión como recepcionista
    client.post('/staff/login', data={
        'username': recepcion_user.username,
        'password': 'recep123'
    })
    
    # Intentar acceder a dashboard de admin (/staff/admin/)
    response = client.get('/staff/admin/', follow_redirects=False)
    assert response.status_code == 302
    assert '/staff/admin/' not in response.headers['Location']

def test_old_pin_route_404(client):
    """Prueba que la ruta vieja del PIN (/verificar-staff) ya no exista y retorne 404."""
    response = client.post('/verificar-staff', json={'pin': '9040'})
    assert response.status_code == 404

def test_login_page_accessible(client):
    """Prueba que /staff/login sea accesible sin autenticación."""
    response = client.get('/staff/login')
    assert response.status_code == 200

def test_wrong_password_rejected(client, admin_user):
    """Prueba que credenciales incorrectas sean rechazadas."""
    # Resetear rate limiting para IP de prueba
    SecurityManager.reset_attempts(f"login_127.0.0.1")

    response = client.post('/staff/login', data={
        'username': admin_user.username,
        'password': 'wrong_password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'incorrectos' in response.get_data(as_text=True).lower()

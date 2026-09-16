import pytest
from flask import url_for
from app.helpers.security import SecurityManager

def test_login_page_renders(client):
    """Verifica que la página de login de staff cargue correctamente (HTTP 200)."""
    response = client.get('/staff/login')
    assert response.status_code == 200
    assert b'Acceso Personal' in response.data or b'login' in response.data.lower()

def test_admin_login_success(client, admin_user):
    """Verifica el login exitoso de un administrador y su redirección a /staff/admin."""
    response = client.post('/staff/login', data={
        'username': admin_user.username,
        'password': 'admin123'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/staff/admin' in response.headers['Location']

def test_recepcion_login_success(client, recepcion_user):
    """Verifica el login exitoso de recepción y su redirección a /staff/recepcion."""
    response = client.post('/staff/login', data={
        'username': recepcion_user.username,
        'password': 'recep123'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/staff/recepcion' in response.headers['Location']

def test_login_failure_invalid_credentials(client, admin_user):
    """Verifica que credenciales incorrectas no permitan el acceso."""
    response = client.post('/staff/login', data={
        'username': admin_user.username,
        'password': 'password_incorrecta'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'incorrectos' in response.get_data(as_text=True).lower()

def test_login_rate_limiting_lockout(client):
    """Verifica que tras 5 intentos fallidos consecutivos se aplique rate limiting."""
    # Resetear cualquier intento previo en la IP del cliente
    ip = '127.0.0.1'
    SecurityManager.reset_attempts(f"login_{ip}")

    # Realizar 5 intentos fallidos
    for i in range(5):
        client.post('/staff/login', data={
            'username': 'usuario_inexistente',
            'password': 'wrong_password'
        })
    
    # El 6º intento debe ser bloqueado por rate limit
    response = client.post('/staff/login', data={
        'username': 'usuario_inexistente',
        'password': 'wrong_password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'bloqueada' in response.get_data(as_text=True).lower()

def test_logout_redirects_to_login(client, admin_user):
    """Verifica que un usuario autenticado pueda cerrar sesión exitosamente."""
    # Iniciar sesión primero
    client.post('/staff/login', data={
        'username': admin_user.username,
        'password': 'admin123'
    })
    
    # Cerrar sesión
    response = client.get('/staff/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/staff/login' in response.headers['Location']

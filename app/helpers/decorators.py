"""
Decoradores de seguridad para el sistema PMS
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Solo permite acceso a usuarios administradores (User con rol='admin')"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Solo User con rol='admin' puede acceder
        from app.models import User
        if not isinstance(current_user, User) or getattr(current_user, 'rol', None) != 'admin':
            flash('Acceso restringido solo para administradores.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def empleado_required(f):
    """Solo permite acceso a empleados con login (Empleado model)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('empleado.login'))
        
        # Solo Empleado puede acceder
        from app.models import Empleado
        if not isinstance(current_user, Empleado):
            flash('Acceso restringido para empleados.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def any_authenticated(f):
    """Permite acceso a cualquier usuario autenticado (admin o empleado)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
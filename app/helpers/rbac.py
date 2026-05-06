from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def empleado_required(f):
    """Decorator para permitir solo empleados y admins"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicie sesión.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Seguridad: Solo permitir roles de staff
        if getattr(current_user, 'rol', None) not in ['admin', 'recepcionista']:
            flash('Acceso denegado. Esta área es exclusiva para el personal.', 'danger')
            return redirect(url_for('cliente.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def any_staff_required(f):
    """Alias para empleado_required"""
    return empleado_required(f)

def admin_required(f):
    """Decorator solo para admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicie sesion.', 'warning')
            return redirect(url_for('auth.login'))
        
        if getattr(current_user, 'rol', None) != 'admin':
            flash('Solo administradores pueden acceder.', 'warning')
            return redirect(url_for('recep.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function
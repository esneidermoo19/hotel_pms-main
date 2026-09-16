from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

STAFF_ROLES = ['admin', 'recepcionista', 'empleado', 'gerente', 'camarero', 'cocinero', 'staff', 'cajero']

def empleado_required(f):
    """Decorator para permitir solo empleados, staff y administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicie sesión.', 'warning')
            return redirect(url_for('staff.login'))
        
        user_role = (getattr(current_user, 'rol', '') or '').strip().lower()
        if user_role == 'cliente':
            flash('Acceso denegado. Esta área es exclusiva para el personal del hotel.', 'danger')
            return redirect(url_for('cliente.home'))
            
        return f(*args, **kwargs)
    return decorated_function

def any_staff_required(f):
    """Alias para empleado_required"""
    return empleado_required(f)

def admin_required(f):
    """Decorator solo para administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicie sesión.', 'warning')
            return redirect(url_for('staff.login'))
        
        user_role = (getattr(current_user, 'rol', '') or '').strip().lower()
        if user_role != 'admin':
            flash('Acceso restringido solo para administradores.', 'warning')
            return redirect(url_for('recep.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function
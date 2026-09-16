from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, Empleado, TurnoEmpleado
from app import db
from app.config import Config
from app.helpers.security import SecurityManager
from datetime import datetime, date
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/gestion-interna-orquidea', methods=['GET', 'POST'])
def login():
    rate_key = f"login_{SecurityManager.get_client_ip()}"

    if request.method == 'POST':
        # Sanitización de entradas
        username = SecurityManager.sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')

        # 1. Verificar Rate Limiting (Bloqueo tras 5 intentos fallidos en 15 min)
        is_blocked, remaining_seconds, _ = SecurityManager.check_rate_limit(rate_key, max_attempts=5, window_seconds=900)
        if is_blocked:
            mins_left = (remaining_seconds // 60) + 1
            SecurityManager.log_audit_event('LOGIN_LOCKOUT', False, username=username, details=f"IP bloqueada por {remaining_seconds}s")
            flash(f'Demasiados intentos fallidos. Por seguridad, su IP ha sido bloqueada temporalmente. Intente en {mins_left} minutos.', 'danger')
            return render_template('auth/login.html')
        
        # Búsqueda insensible a mayúsculas/minúsculas
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
        
        if user and user.activo and user.check_password(password):
            # Seguridad: Impedir que clientes entren al panel de staff
            if user.rol == 'cliente':
                SecurityManager.log_audit_event('LOGIN_DENIED_CLIENT', False, username=username, details="Cliente intentó ingresar a portal staff")
                flash('Acceso denegado. Este portal es exclusivo para el personal.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            SecurityManager.reset_attempts(rate_key)
            SecurityManager.log_audit_event('LOGIN_SUCCESS', True, username=user.username, details=f"Rol: {user.rol}")
            
            # Registrar hora de entrada si es empleado
            if user.rol != 'admin':
                empleado = Empleado.query.filter_by(user_id=user.id).first()
                if empleado:
                    now = datetime.now()
                    empleado.hora_entrada = now
                    db.session.flush()
                    
                    # Crear registro de turno
                    turno = TurnoEmpleado(
                        empleado_id=empleado.id,
                        fecha=now.date(),
                        hora_entrada=now,
                        estado='activo'
                    )
                    db.session.add(turno)
                    db.session.commit()
            
            flash('¡Bienvenido!', 'success')
            if user.rol == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('recep.dashboard'))
        else:
            SecurityManager.record_failed_attempt(rate_key)
            SecurityManager.log_audit_event('LOGIN_FAILED', False, username=username, details="Usuario o contraseña incorrectos")
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    now = datetime.now()
    user = current_user
    
    # Registrar hora de salida si es empleado
    if user.rol != 'admin':
        empleado = Empleado.query.filter_by(user_id=user.id).first()
        if empleado:
            empleado.hora_salida = now
            
            # Cerrar registro de turno
            turno = TurnoEmpleado.query.filter_by(
                empleado_id=empleado.id,
                fecha=now.date(),
                estado='activo'
            ).first()
            if turno:
                turno.hora_salida = now
                turno.horas = turno.calcular_horas()
                turno.estado = 'completado'
            
            db.session.commit()
    
    SecurityManager.log_audit_event('LOGOUT', True, username=user.username, details="Sesión cerrada correctamente")
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verificar-staff', methods=['POST'])
def verificar_staff():
    """Valida el PIN de acceso al portal de personal utilizando un hash seguro y rate limiting por IP"""
    data = request.get_json() or {}
    pin_ingresado = SecurityManager.sanitize_input(data.get('pin', ''), max_length=10)
    
    pin_rate_key = f"staff_pin_{SecurityManager.get_client_ip()}"
    
    # 1. Verificar Rate Limiting por IP (Máximo 5 intentos por 15 minutos)
    is_blocked, remaining_seconds, _ = SecurityManager.check_rate_limit(pin_rate_key, max_attempts=5, window_seconds=900)
    if is_blocked:
        mins_left = (remaining_seconds // 60) + 1
        SecurityManager.log_audit_event('STAFF_PIN_LOCKOUT', False, details=f"IP bloqueada por {remaining_seconds}s")
        return jsonify({
            'success': False, 
            'message': f'Demasiados intentos fallidos. Intente nuevamente en {mins_left} minutos.'
        }), 429
    
    # 2. Validación de PIN mediante Hash Seguro (evita comparación en texto plano)
    if pin_ingresado and check_password_hash(Config.STAFF_PIN_HASH, pin_ingresado):
        SecurityManager.reset_attempts(pin_rate_key)
        SecurityManager.log_audit_event('STAFF_PIN_SUCCESS', True, details="PIN de personal verificado")
        session['staff_access_verified'] = True
        return jsonify({'success': True, 'redirect': url_for('auth.login')})
    else:
        SecurityManager.record_failed_attempt(pin_rate_key)
        SecurityManager.log_audit_event('STAFF_PIN_FAILED', False, details="PIN incorrecto ingresado")
        return jsonify({'success': False, 'message': 'PIN incorrecto.'}), 401
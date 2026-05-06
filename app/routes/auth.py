from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Empleado, TurnoEmpleado
from app import db
from datetime import datetime, date
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/gestion-interna-orquidea', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Búsqueda insensible a mayúsculas/minúsculas
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
        
        if user and user.activo and user.check_password(password):
            # Seguridad: Impedir que clientes entren al panel de staff
            if user.rol == 'cliente':
                flash('Acceso denegado. Este portal es exclusivo para el personal.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            
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
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    now = datetime.now()
    
    # Registrar hora de salida si es empleado
    if current_user.rol != 'admin':
        empleado = Empleado.query.filter_by(user_id=current_user.id).first()
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
    
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verificar-staff', methods=['POST'])
def verificar_staff():
    """Valida el PIN de acceso al portal de personal desde el servidor"""
    from flask import session, jsonify
    data = request.get_json()
    pin_ingresado = data.get('pin')
    
    # PIN secreto almacenado solo en el servidor
    PIN_SECRETO = "9040"
    
    # Implementar un límite de intentos básico por sesión
    intentos = session.get('staff_pin_attempts', 0)
    
    if intentos >= 5:
        return jsonify({'success': False, 'message': 'Demasiados intentos. Intente más tarde.'}), 429
    
    if pin_ingresado == PIN_SECRETO:
        session['staff_pin_attempts'] = 0 # Reiniciar
        session['staff_access_verified'] = True # Bandera temporal
        return jsonify({'success': True, 'redirect': url_for('auth.login')})
    else:
        session['staff_pin_attempts'] = intentos + 1
        return jsonify({'success': False, 'message': 'PIN incorrecto.'}), 401
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Empleado, TurnoEmpleado
from app import db
from datetime import datetime, date

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
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
            Empleado.hora_salida = now
            
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
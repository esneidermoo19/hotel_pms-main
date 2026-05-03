from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import Habitacion, Reservacion, ConfigHotel
from app.services.email_service import EmailService
from app import db
from datetime import datetime, timedelta

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/')
def home():
    return render_template('cliente/welcome.html')

@cliente_bp.route('/habitaciones', methods=['GET', 'POST'])
def habitaciones():
    habitaciones = Habitacion.query.all()
    
    if request.method == 'POST':
        habitacion_id = request.form.get('habitacion_id')
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str = request.form.get('fecha_fin')
        
        habitacion = Habitacion.query.get_or_404(habitacion_id)
        
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            flash('Fechas inválidas.', 'danger')
            return redirect(url_for('cliente.habitaciones'))
        
        if fecha_inicio >= fecha_fin:
            flash('La fecha de inicio debe ser anterior a la fecha de fin.', 'danger')
            return redirect(url_for('cliente.habitaciones'))
        
        if fecha_inicio.date() < datetime.now().date():
            flash('La fecha de inicio no puede ser anterior a hoy.', 'danger')
            return redirect(url_for('cliente.habitaciones'))
        
        # 1. Validar Límites Diarios (Máximo 4 por IP o Email)
        email = request.form.get('email', '').strip()
        if current_user.is_authenticated:
            email = current_user.email
        
        ip_addr = request.remote_addr
        hace_24h = datetime.now() - timedelta(days=1)
        
        conteo_reservas = Reservacion.query.filter(
            ((Reservacion.email_cliente == email) | (Reservacion.ip_address == ip_addr)),
            Reservacion.fecha_creacion >= hace_24h
        ).count()
        
        if conteo_reservas >= 4:
            flash('Has alcanzado el límite máximo de 4 reservas por día. Inténtalo de nuevo mañana.', 'warning')
            return redirect(url_for('cliente.habitaciones'))
        
        # 2. Verificar Disponibilidad
        reserva_existente = Reservacion.query.filter(
            Reservacion.habitacion_id == habitacion_id,
            Reservacion.estado == 'activa',
            ((Reservacion.fecha_inicio <= fecha_fin) & (Reservacion.fecha_fin >= fecha_inicio))
        ).first()
        
        if reserva_existente:
            flash('La habitación no está disponible en las fechas seleccionadas.', 'danger')
            return redirect(url_for('cliente.habitaciones'))
        
        # 3. Crear Reserva en estado 'pendiente_pago'
        reserva = Reservacion(
            habitacion_id=habitacion_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado='pendiente_pago',
            codigo=Reservacion.generar_codigo(),
            ip_address=ip_addr
        )
        
        # Calcular Total
        noches = (fecha_fin - fecha_inicio).days
        reserva.total_pago = noches * habitacion.precio_noche
        
        if current_user.is_authenticated:
            reserva.usuario_id = current_user.id
            reserva.nombre_cliente = current_user.nombre
            reserva.email_cliente = current_user.email
            reserva.telefono_cliente = current_user.telefono
        else:
            nombre = request.form.get('nombre', '').strip()
            telefono = request.form.get('telefono', '').strip()
            
            if not nombre or not email or not telefono:
                flash('Debe completar todos los datos personales.', 'danger')
                return redirect(url_for('cliente.habitaciones'))
            
            reserva.nombre_cliente = nombre
            reserva.email_cliente = email
            reserva.telefono_cliente = telefono
        
        db.session.add(reserva)
        db.session.commit()
        
        return redirect(url_for('cliente.pago', reserva_id=reserva.id))
    
    return render_template('cliente/home.html', habitaciones=habitaciones)

@cliente_bp.route('/pago/<int:reserva_id>')
def pago(reserva_id):
    reserva = Reservacion.query.get_or_404(reserva_id)
    if reserva.estado != 'pendiente_pago':
        return redirect(url_for('cliente.home'))
    
    habitacion = Habitacion.query.get(reserva.habitacion_id)
    noches = (reserva.fecha_fin - reserva.fecha_inicio).days
    
    return render_template('cliente/pago.html', reserva=reserva, habitacion=habitacion, noches=noches)

@cliente_bp.route('/procesar_pago/<int:reserva_id>', methods=['POST'])
def procesar_pago(reserva_id):
    reserva = Reservacion.query.get_or_404(reserva_id)
    if reserva.estado != 'pendiente_pago':
        return redirect(url_for('cliente.home'))
    
    metodo = request.form.get('metodo_pago', 'mastercard')
    reserva.metodo_pago = metodo
    
    # Simulación de éxito de pago
    # Si es efectivo, podríamos dejarlo como pendiente, pero para el flujo del cliente 
    # diremos que la reserva está confirmada pero pendiente de cobro físico.
    reserva.estado = 'activa'
    if metodo != 'efectivo':
        reserva.pagado = True
    
    db.session.commit()
    
    # Enviar Email de confirmación
    habitacion = Habitacion.query.get(reserva.habitacion_id)
    config = ConfigHotel.query.first()
    EmailService.enviar_codigo_reserva(reserva, habitacion, config)
    
    flash(f'¡Pago exitoso! Su reserva ha sido confirmada. Hemos enviado el código de acceso a: {reserva.email_cliente}', 'success')
    return redirect(url_for('cliente.home'))

@cliente_bp.route('/mis_reservas')
@login_required
def mis_reservas():
    reservas = Reservacion.query.filter_by(usuario_id=current_user.id, estado='activa').all()
    return render_template('cliente/reservas.html', reservas=reservas)

@cliente_bp.route('/cancelar_codigo', methods=['GET', 'POST'])
def cancelar_codigo():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        reserva = Reservacion.query.filter_by(codigo=codigo, estado='activa').first()
        
        if not reserva:
            flash('Código de reserva no encontrado.', 'danger')
            return redirect(url_for('cliente.cancelar_codigo'))
        
        reserva.estado = 'cancelada'
        db.session.commit()
        
        flash('Reserva cancelada exitosamente.', 'success')
        return redirect(url_for('cliente.home'))
    
    return render_template('cliente/cancelar.html')

@cliente_bp.route('/cancelar/<int:reserva_id>')
@login_required
def cancelar(reserva_id):
    reserva = Reservacion.query.get_or_404(reserva_id)
    
    if reserva.usuario_id != current_user.id:
        flash('No tiene permiso para cancelar esta reserva.', 'danger')
        return redirect(url_for('cliente.mis_reservas'))
    
    reserva.estado = 'cancelada'
    db.session.commit()
    
    flash('Reserva cancelada exitosamente.', 'success')
    return redirect(url_for('cliente.mis_reservas'))

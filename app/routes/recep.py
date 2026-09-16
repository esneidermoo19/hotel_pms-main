from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Habitacion, Reservacion, Empleado
from app import db
from datetime import datetime
from flask_login import login_required, current_user
from app.helpers.rbac import empleado_required
import json

recep_bp = Blueprint('recep', __name__)

@recep_bp.route('/')
@empleado_required
def index():
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/dashboard')
@empleado_required
def dashboard():
    from app.models import TurnoEmpleado
    
    habitaciones_libres = Habitacion.query.filter_by(estado='Disponible').all()
    habitaciones_ocupadas = Habitacion.query.filter_by(estado='Ocupada').all()
    habitaciones_mantenimiento = Habitacion.query.filter_by(estado='Mantenimiento').all()
    
    ocupadas_pendientes = []
    ocupadas_pagadas = []
    
    for hab in habitaciones_ocupadas:
        reserva = Reservacion.query.filter_by(habitacion_id=hab.id).order_by(Reservacion.id.desc()).first()
        if reserva:
            item = {'habitacion': hab, 'reserva': reserva}
            if hasattr(reserva, 'pagado') and reserva.pagado:
                ocupadas_pagadas.append(item)
            else:
                ocupadas_pendientes.append(item)
                
    # Reservas hechas por huéspedes (online) activas o pendientes de pago
    reservas_online = Reservacion.query.filter(
        Reservacion.estado.in_(['activa', 'pendiente_pago'])
    ).order_by(Reservacion.fecha_creacion.desc()).all()

    # Obtener o vincular perfil de empleado del usuario en sesión
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if not empleado and hasattr(current_user, 'nombre'):
        empleado = Empleado.query.filter_by(nombre=current_user.nombre).first()
        if empleado and not empleado.user_id:
            empleado.user_id = current_user.id
            db.session.commit()
            
    if not empleado:
        try:
            empleado = Empleado(
                nombre=current_user.nombre or current_user.username,
                email=current_user.email,
                telefono=current_user.telefono,
                cargo=current_user.rol.capitalize() if current_user.rol else 'Recepcionista',
                activo=True,
                user_id=current_user.id
            )
            db.session.add(empleado)
            db.session.commit()
        except Exception:
            db.session.rollback()
            empleado = None

    hoy_date = datetime.now().date()
    turno_activo = None
    if empleado:
        turno_activo = TurnoEmpleado.query.filter_by(
            empleado_id=empleado.id, 
            hora_salida=None,
            fecha=hoy_date
        ).first()
    
    reservas_verificacion = Reservacion.query.filter_by(estado='pendiente_verificacion').order_by(Reservacion.fecha_creacion.desc()).all()
    
    return render_template(
        'recepcion/dashboard.html', 
        libres=habitaciones_libres, 
        occupations_no_pagadas=ocupadas_pendientes,
        occupations_pagadas=ocupadas_pagadas,
        mantenimiento=habitaciones_mantenimiento,
        reservas_online=reservas_online,
        reservas_verificacion=reservas_verificacion,
        turno_activo=turno_activo,
        empleado=empleado
    )

@recep_bp.route('/reserva/checkin/<int:reservacion_id>', methods=['POST'])
@empleado_required
def checkin_reserva(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    reserva.estado = 'activa'
    if reserva.habitacion:
        reserva.habitacion.estado = 'Ocupada'
    db.session.commit()
    flash(f'Check-in completado exitosamente para {reserva.nombre_cliente} en Habitación #{reserva.habitacion.numero if reserva.habitacion else ""}.', 'success')
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/reserva/cancelar_staff/<int:reservacion_id>', methods=['POST'])
@empleado_required
def cancelar_reserva_staff(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    reserva.estado = 'cancelada'
    if reserva.habitacion and reserva.habitacion.estado == 'Ocupada':
        reserva.habitacion.estado = 'Disponible'
    db.session.commit()
    flash(f'Reserva {reserva.codigo} cancelada por recepción.', 'info')
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/reserva/verificar_pago/<int:reservacion_id>', methods=['POST'])
@empleado_required
def verificar_pago(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    accion = request.form.get('accion')
    
    if accion == 'aprobar':
        reserva.estado = 'activa'
        reserva.pagado = True
        if reserva.habitacion and reserva.fecha_inicio.date() <= datetime.now().date():
            reserva.habitacion.estado = 'Ocupada'
        flash(f'Pago aprobado para la reserva {reserva.codigo}.', 'success')
    elif accion == 'rechazar':
        reserva.estado = 'cancelada'
        flash(f'Pago rechazado para la reserva {reserva.codigo}. Reserva cancelada.', 'danger')
        
    db.session.commit()
    
    if request.form.get('from_admin') == '1':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('recep.dashboard'))


@recep_bp.route('/turno/empezar', methods=['POST'])
@empleado_required
def empezar_turno():
    from app.models import TurnoEmpleado
    
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if not empleado and hasattr(current_user, 'nombre'):
        empleado = Empleado.query.filter_by(nombre=current_user.nombre).first()
        
    if not empleado:
        try:
            empleado = Empleado(
                nombre=current_user.nombre or current_user.username,
                email=current_user.email,
                telefono=current_user.telefono,
                cargo=current_user.rol.capitalize() if current_user.rol else 'Recepcionista',
                activo=True,
                user_id=current_user.id
            )
            db.session.add(empleado)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al vincular perfil de empleado: {e}', 'danger')
            return redirect(url_for('recep.dashboard'))
        
    hoy_date = datetime.now().date()
    turno_existente = TurnoEmpleado.query.filter_by(
        empleado_id=empleado.id, 
        hora_salida=None,
        fecha=hoy_date
    ).first()
    
    if turno_existente:
        flash('Ya tienes un turno activo en este momento.', 'warning')
        return redirect(url_for('recep.dashboard'))
        
    now = datetime.now()
    nuevo_turno = TurnoEmpleado(
        empleado_id=empleado.id,
        fecha=hoy_date,
        hora_entrada=now,
        estado='activo'
    )
    db.session.add(nuevo_turno)
    db.session.commit()
    
    hora_str = now.strftime('%H:%M')
    flash(f'¡Turno iniciado exitosamente a las {hora_str}! Registro de asistencia visible en Administración.', 'success')
    return redirect(url_for('recep.dashboard'))


@recep_bp.route('/turno/finalizar', methods=['POST'])
@empleado_required
def finalizar_turno():
    from app.models import TurnoEmpleado
    
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if not empleado and hasattr(current_user, 'nombre'):
        empleado = Empleado.query.filter_by(nombre=current_user.nombre).first()
        
    if not empleado:
        flash('No se encontró perfil de empleado activo.', 'danger')
        return redirect(url_for('recep.dashboard'))
        
    hoy_date = datetime.now().date()
    turno_activo = TurnoEmpleado.query.filter_by(
        empleado_id=empleado.id, 
        hora_salida=None,
        fecha=hoy_date
    ).first()
    
    if not turno_activo:
        flash('No tienes ningún turno activo para finalizar.', 'warning')
        return redirect(url_for('recep.dashboard'))
        
    now = datetime.now()
    turno_activo.hora_salida = now
    turno_activo.horas = turno_activo.calcular_horas()
    turno_activo.estado = 'completado'
    db.session.commit()
    
    hora_str = now.strftime('%H:%M')
    horas_str = f"{turno_activo.horas:.1f}"
    flash(f'¡Turno finalizado a las {hora_str}! Se registraron {horas_str} horas trabajadas.', 'info')
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/habitacion/estado/<int:habitacion_id>', methods=['POST'])
@empleado_required
def cambiar_estado_habitacion(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado in ['Disponible', 'Ocupada', 'Mantenimiento']:
        habitacion.estado = nuevo_estado
        db.session.commit()
        flash(f'Habitación {habitacion.numero} actualizada a {nuevo_estado}.', 'success')
    else:
        flash('Estado no válido.', 'danger')
    
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/reserva/pago/<int:reservacion_id>', methods=['POST'])
@empleado_required
def actualizar_pago(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    pagado = request.form.get('pagado') == 'si'
    
    reserva.pagado = pagado
    
    # También actualizar el estado de la habitación
    if pagado and reserva.habitacion:
        reserva.habitacion.estado = 'Ocupada'
    
    db.session.commit()
    flash(f'Estado de pago actualizado para {reserva.nombre_cliente}.', 'success')
    
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/reservar/<int:habitacion_id>', methods=['GET', 'POST'])
@empleado_required
def hacer_reserva(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    
    # Check if the room is currently in maintenance or occupied
    if habitacion.estado == 'Mantenimiento':
        flash('Esta habitación está en mantenimiento.', 'danger')
        return redirect(url_for('recep.dashboard'))

    if request.method == 'POST':
        try:
            nombre_huesped = request.form.get('nombre_huesped')
            telefono_huesped = request.form.get('telefono_huesped')
            email_huesped = request.form.get('email_huesped')
            cedula_nit = request.form.get('cedula_nit')
            tipo_documento = request.form.get('tipo_documento', 'cedula')
            num_personas = int(request.form.get('num_personas', 1))
            hay_menores = request.form.get('hay_menores', 'no')
            menores = int(request.form.get('menores', 0)) if hay_menores == 'si' else 0
            
            fecha_ingreso_str = request.form.get('fecha_ingreso')
            fecha_salida_str = request.form.get('fecha_salida')
            
            if not nombre_huesped or not telefono_huesped or not cedula_nit:
                flash('Debe completar todos los datos del huésped (Nombre, Teléfono, Cédula/NIT).', 'warning')
                return redirect(url_for('recep.hacer_reserva', habitacion_id=habitacion.id))
            
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d')
            fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
            
            # Check for existing reservation conflicts
            conflicto = Reservacion.query.filter(
                Reservacion.habitacion_id == habitacion.id,
                Reservacion.estado == 'activa',
                ((Reservacion.fecha_inicio <= fecha_salida) & (Reservacion.fecha_fin >= fecha_ingreso))
            ).first()
            
            if conflicto:
                flash(f'Conflicto de fechas: Ya existe una reserva para {conflicto.nombre_cliente} del {conflicto.fecha_inicio.strftime("%d/%m")} al {conflicto.fecha_fin.strftime("%d/%m")}.', 'danger')
                return redirect(url_for('recep.hacer_reserva', habitacion_id=habitacion.id))
            
            dias_estadia = (fecha_salida - fecha_ingreso).days
            if dias_estadia <= 0:
                flash('La fecha de salida debe ser mayor a la de ingreso.', 'warning')
                return redirect(url_for('recep.hacer_reserva', habitacion_id=habitacion.id))
                
            total_pago = dias_estadia * habitacion.precio_noche
            
            datos_menores = []
            for i in range(1, menores + 1):
                nombre_menor = request.form.get(f'menor_nombre_{i}')
                edad_menor = request.form.get(f'menor_edad_{i}')
                if nombre_menor and edad_menor:
                    datos_menores.append({'nombre': nombre_menor, 'edad': int(edad_menor)})
            datos_menores_json = json.dumps(datos_menores) if datos_menores else None
            
            empleado = Empleado.query.filter_by(user_id=current_user.id).first()
            
            nueva_reserva = Reservacion(
                usuario_id=current_user.id,
                habitacion_id=habitacion.id,
                fecha_inicio=fecha_ingreso,
                fecha_fin=fecha_salida,
                total_pago=total_pago,
                nombre_cliente=nombre_huesped,
                telefono_cliente=telefono_huesped,
                email_cliente=email_huesped,
                cedula_nit=cedula_nit,
                tipo_documento=tipo_documento,
                num_personas=num_personas,
                menores=menores,
                datos_menores=datos_menores_json,
                empleado_id=empleado.id if empleado else None,
                codigo=Reservacion.generar_codigo()
            )
            db.session.add(nueva_reserva)
            
            # Change room status only if it's for today
            if fecha_ingreso.date() <= datetime.now().date():
                habitacion.estado = 'Ocupada'
            
            db.session.commit()
            
            flash(f'¡Reserva confirmada! Habitación {habitacion.numero} asignada a {nombre_huesped}.', 'success')
            return redirect(url_for('recep.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al guardar: {str(e)}', 'danger')
    
    return render_template('recepcion/formulario_reserva.html', habitacion=habitacion)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Habitacion, Reservacion
from app import db
from datetime import datetime
from flask_login import login_required, current_user
import json

recep_bp = Blueprint('recep', __name__)

@recep_bp.route('/')
@login_required
def index():
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/dashboard')
@login_required
def dashboard():
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
    
    return render_template(
        'recepcion/dashboard.html', 
       libres=habitaciones_libres, 
        occupations_no_pagadas=ocupadas_pendientes,
        occupations_pagadas=ocupadas_pagadas,
        mantenimiento=habitaciones_mantenimiento
    )
    
    return render_template(
        'recepcion/dashboard.html', 
        libres=habitaciones_libres, 
        occupations_no_pagadas=ocupadas_pendientes,
        occupations_pagadas=ocupadas_pagadas,
        mantenimiento=habitaciones_mantenimiento
    )

@recep_bp.route('/habitacion/estado/<int:habitacion_id>', methods=['POST'])
@login_required
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
@login_required
def actualizar_pago(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    pagado = request.form.get('pagado') == 'si'
    
    reserva.pagado = pagado
    
    # También actualizar el estado de la habitación
    if pagado and reserva.habitacion:
        reserva.habitacion.estado = 'Ocupada'
    
    db.session.commit()
    flash(f'Estado de pago actualizado para {reserva.nombre_huesped}.', 'success')
    
    return redirect(url_for('recep.dashboard'))

@recep_bp.route('/reservar/<int:habitacion_id>', methods=['GET', 'POST'])
@login_required
def hacer_reserva(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    
    if habitacion.estado != 'Disponible':
        flash('Esta habitación ya fue ocupada.', 'danger')
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
            
            datos_menores = []
            for i in range(1, menores + 1):
                nombre_menor = request.form.get(f'menor_nombre_{i}')
                edad_menor = request.form.get(f'menor_edad_{i}')
                if nombre_menor and edad_menor:
                    datos_menores.append({
                        'nombre': nombre_menor,
                        'edad': int(edad_menor)
                    })
            datos_menores_json = json.dumps(datos_menores) if datos_menores else None
            
            fecha_ingreso_str = request.form.get('fecha_ingreso')
            fecha_salida_str = request.form.get('fecha_salida')
            
            if not nombre_huesped or not telefono_huesped or not cedula_nit:
                flash('Debe completar todos los datos del huésped (Nombre, Teléfono, Cédula/NIT).', 'warning')
                return redirect(url_for('recep.hacer_reserva', habitacion_id=habitacion.id))
            
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d')
            fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
            
            dias_estadia = (fecha_salida - fecha_ingreso).days
            if dias_estadia <= 0:
                flash('La fecha de salida debe ser mayor a la de ingreso.', 'warning')
                return redirect(url_for('recep.hacer_reserva', habitacion_id=habitacion.id))
                
            total_pago = dias_estadia * habitacion.precio_noche
            
            nueva_reserva = Reservacion(
                huesped_id=current_user.id,
                habitacion_id=habitacion.id,
                fecha_ingreso=fecha_ingreso,
                fecha_salida=fecha_salida,
                total_pago=total_pago,
                nombre_huesped=nombre_huesped,
                telefono_huesped=telefono_huesped,
                email_huesped=email_huesped,
                cedula_nit=cedula_nit,
                tipo_documento=tipo_documento,
                num_personas=num_personas,
                menores=menores,
                datos_menores=datos_menores_json,
                empleado_id=current_user.id
            )
            db.session.add(nueva_reserva)
            
            habitacion.estado = 'Ocupada'
            
            db.session.commit()
            
            flash(f'¡Reserva confirmada! Habitación {habitacion.numero} asignada a {nombre_huesped}.', 'success')
            return redirect(url_for('recep.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al guardar: {str(e)}', 'danger')

    return render_template('recepcion/formulario_reserva.html', habitacion=habitacion)
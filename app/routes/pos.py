from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import Habitacion, Reservacion, ConsumoPOS, Empleado
from app import db
from datetime import datetime
from flask_login import login_required, current_user

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/caja')
@login_required
def caja_principal():
    habitaciones_ocupadas = Habitacion.query.filter_by(estado='Ocupada').all()
    
    reservas_activas = []
    for hab in habitaciones_ocupadas:
        reserva = Reservacion.query.filter_by(habitacion_id=hab.id).order_by(Reservacion.id.desc()).first()
        if reserva:
            reservas_activas.append({
                'habitacion': hab,
                'reserva_id': reserva.id
            })
    
    return render_template('pos/caja.html', activas=reservas_activas)

@pos_bp.route('/cargar_consumo/<int:reserva_id>', methods=['GET', 'POST'])
@login_required
def cargar_consumo(reserva_id):
    reserva = Reservacion.query.get_or_404(reserva_id)
    habitacion = Habitacion.query.get(reserva.habitacion_id)
    empleados = Empleado.query.filter_by(activo=True).order_by(Empleado.nombre).all()
    
    current_empleado_id = current_user.id
    
    if request.method == 'POST':
        try:
            producto_nombre = request.form.get('producto')
            monto_str = request.form.get('monto')
            empleado_id = request.form.get('empleado_id')
            
            if not monto_str or float(monto_str) <= 0:
                flash('El monto debe ser un número mayor a cero.', 'warning')
                return redirect(url_for('pos.cargar_consumo', reserva_id=reserva.id))
                
            monto = float(monto_str)

            nuevo_consumo = ConsumoPOS(
                reservacion_id=reserva.id,
                producto=producto_nombre,
                monto=monto,
                empleado_id=empleado_id if empleado_id else None
            )
            db.session.add(nuevo_consumo)

            reserva.total_pago += monto
            
            db.session.commit()

            flash(f'Cargo de ${monto} por "{producto_nombre}" añadido a la Habitación {habitacion.numero}.', 'success')
            return redirect(url_for('pos.caja_principal'))

        except ValueError:
             flash('Por favor, ingresa un valor numérico válido para el monto.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al procesar el cargo: {str(e)}', 'danger')

    historial_consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).order_by(ConsumoPOS.fecha.desc()).all()

    return render_template(
        'pos/cargar_consumo.html', 
        reserva=reserva, 
        habitacion=habitacion,
        historial=historial_consumos,
        empleados=empleados,
        current_user_id=current_user.id,
        current_user_nombre=current_user.nombre
    )
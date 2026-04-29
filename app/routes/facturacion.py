from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Habitacion, Reservacion, ConsumoPOS, ConfigHotel
from app.services.facturacion_service import FacturacionService
from flask_login import login_required
from app import db

facturacion_bp = Blueprint('facturacion', __name__)

@facturacion_bp.route('/checkout/<int:habitacion_id>', methods=['GET', 'POST'])
@login_required
def realizar_checkout(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    reserva = Reservacion.query.filter_by(habitacion_id=habitacion.id).order_by(Reservacion.id.desc()).first()
    
    if not reserva:
        flash('No se encontró una reserva para esta habitación.', 'warning')
        return redirect(url_for('recep.dashboard'))

    config = ConfigHotel.query.first() or ConfigHotel()
    consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).all()
    
    total_extras = sum(c.monto for c in consumos)
    costo_noches = reserva.total_pago - total_extras

    if request.method == 'POST':
        try:
            metodo_pago = request.form.get('metodo_pago', 'Efectivo')
            nueva_factura = FacturacionService.realizar_checkout(habitacion_id, metodo_pago)
            
            flash(f'Check-out completado. Factura {nueva_factura.numero_factura} generada con éxito.', 'success')
            return redirect(url_for('reportes.imprimir_factura', factura_id=nueva_factura.id))
            
        except Exception as e:
            flash(f'Error al procesar la facturación: {str(e)}', 'danger')

    return render_template('facturacion/factura.html', 
        reserva=reserva, 
        habitacion=habitacion,
        consumos=consumos,
        costo_noches=costo_noches,
        total_extras=total_extras,
        config=config
    )
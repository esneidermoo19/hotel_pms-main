from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import Habitacion, Reservacion, ConsumoPOS, Factura, ConfigHotel, ClienteFactura
from app import db, mail
from flask_mail import Message
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from app.helpers.rbac import admin_required, empleado_required
from sqlalchemy import func

reportes_bp = Blueprint('reportes', __name__)

def enviar_factura_email(factura, reserva, habitacion, config):
    """Envía la factura por correo electrónico"""
    if not reserva.email_huesped:
        return False
    
    try:
        noches = (reserva.fecha_salida - reserva.fecha_ingreso).days
        consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).all()
        total_extras = sum(c.monto for c in consumos)
        
        html_factura = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ccc;">
            <div style="text-align: center; border-bottom: 2px solid #4a235a; padding-bottom: 15px; margin-bottom: 20px;">
                <h1 style="color: #1F1528; margin: 10px 0;">{config.nombre}</h1>
                <p>NIT: {config.nit}</p>
                <p>{config.direccion}, {config.ciudad}</p>
                <p>Tel: {config.telefono}</p>
            </div>
            
            <h2 style="background: #4a235a; color: white; padding: 10px; text-align: center;">FACTURA ELECTRÓNICA</h2>
            <p style="text-align: center; font-weight: bold;">No. {factura.numero_factura}</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><strong>Nombre:</strong> {reserva.nombre_huesped}</p>
                <p><strong>Documento:</strong> {reserva.tipo_documento}: {reserva.cedula_nit}</p>
                <p><strong>Habitación:</strong> {habitacion.numero} ({habitacion.tipo})</p>
                <p><strong>Estancia:</strong> {reserva.fecha_ingreso.strftime('%Y-%m-%d')} a {reserva.fecha_salida.strftime('%Y-%m-%d')} ({noches} noches)</p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background: #4a235a; color: white;">
                    <th style="padding: 10px; text-align: left;">Concepto</th>
                    <th style="padding: 10px; text-align: right;">Valor</th>
                </tr>
                <tr><td style="padding: 10px;">Alojamiento ({noches} noches)</td>
                    <td style="padding: 10px; text-align: right;">{int(factura.total - total_extras):,} COP</td></tr>
        """
        
        for c in consumos:
            html_factura += f"<tr><td style='padding: 10px;'>{c.producto}</td><td style='padding: 10px; text-align: right;'>{int(c.monto):,} COP</td></tr>"
        
        html_factura += f"""
                <tr style="background: #f8f9fa; font-weight: bold;">
                    <td style="padding: 15px;">TOTAL PAGADO</td>
                    <td style="padding: 15px; text-align: right; color: #4a235a; font-size: 18px;">{int(factura.total):,} COP</td>
                </tr>
            </table>
            
            <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #ccc; font-size: 12px; color: #666;">
                <p>Gracias por su preferencia</p>
                <p>{config.nombre} - {config.ciudad}</p>
                <p>{config.email} - {config.web}</p>
            </div>
        </div>
        """
        
        from flask import current_app
        sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        msg = Message(
            subject=f"Factura {factura.numero_factura} - {config.nombre}",
            sender=sender,
            recipients=[reserva.email_huesped],
            html=html_factura
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False



@reportes_bp.route('/historial')
@empleado_required
def historial():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    habitacion_id = request.args.get('habitacion_id')
    
    query = Reservacion.query
    
    if fecha_inicio:
        query = query.filter(Reservacion.fecha_creacion >= datetime.strptime(fecha_inicio, '%Y-%m-%d'))
    if fecha_fin:
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Reservacion.fecha_creacion < fin)
    if habitacion_id and habitacion_id != '':
        query = query.filter(Reservacion.habitacion_id == int(habitacion_id))
    
    reservas = query.order_by(Reservacion.fecha_creacion.desc()).all()
    
    habitaciones = Habitacion.query.all()
    
    total_ingresos = sum(r.total_pago for r in reservas)
    
    return render_template('reportes/historial.html', 
                         reservas=reservas, 
                         habitaciones=habitaciones,
                         total_ingresos=total_ingresos,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         habitacion_id=habitacion_id)

@reportes_bp.route('/resumen_diario')
@admin_required
def resumen_diario():
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
    
    reservas = Reservacion.query.filter(
        Reservacion.fecha_creacion >= fecha_dt,
        Reservacion.fecha_creacion < fecha_dt + timedelta(days=1)
    ).all()
    
    ingresos_noches = sum(r.total_pago for r in reservas)
    
    consumos = ConsumoPOS.query.join(Reservacion).filter(
        Reservacion.fecha_creacion >= fecha_dt,
        Reservacion.fecha_creacion < fecha_dt + timedelta(days=1)
    ).all()
    
    ingresos_pos = sum(c.monto for c in consumos)
    
    habitaciones = Habitacion.query.all()
    
    detalle_habitaciones = []
    for hab in habitaciones:
        reservas_hab = [r for r in reservas if r.habitacion_id == hab.id]
        consumos_hab = [c for c in consumos if c.reservacion.habitacion_id == hab.id]
        total_hab = sum(r.total_pago for r in reservas_hab) + sum(c.monto for c in consumos_hab)
        if total_hab > 0:
            detalle_habitaciones.append({
                'habitacion': hab,
                'reservas': reservas_hab,
                'consumos': consumos_hab,
                'total': total_hab
            })
    
    total_dia = ingresos_noches + ingresos_pos
    
    return render_template('reportes/resumen_diario.html',
                         fecha=fecha,
                         reservas=reservas,
                         consumos=consumos,
                         ingresos_noches=ingresos_noches,
                         ingresos_pos=ingresos_pos,
                         total_dia=total_dia,
                         detalle_habitaciones=detalle_habitaciones)

@reportes_bp.route('/facturacion')
@empleado_required
def facturacion():
    reservacion_id = request.args.get('reservacion_id')
    reservas_activas = Reservacion.query.filter_by(estado='activa').all()
    
    config = ConfigHotel.query.first()
    if not config:
        config = ConfigHotel()
        db.session.add(config)
        db.session.commit()
    
    if reservacion_id:
        reserva = Reservacion.query.get_or_404(reservacion_id)
        habitacion = Habitacion.query.get(reserva.habitacion_id)
        consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).all()
        
        total_extras = sum(c.monto for c in consumos)
        costo_noches = reserva.total_pago - total_extras
        
        return render_template('reportes/factura_imprimir.html',
                             reserva=reserva,
                             habitacion=habitacion,
                             consumos=consumos,
                             costo_noches=costo_noches,
                             total_extras=total_extras,
                             config=config,
                             factura=None)
    
    return render_template('reportes/facturacion.html', reservas_activas=reservas_activas)

@reportes_bp.route('/generar_factura', methods=['POST'])
@empleado_required
def generar_factura():
    try:
        reservacion_id = request.form.get('reservacion_id')
        reserva = Reservacion.query.get_or_404(reservacion_id)
        
        direccion = request.form.get('direccion_cliente', '')
        metodo_pago = request.form.get('metodo_pago', 'Efectivo')
        enviar_email = request.form.get('enviar_email', 'no') == 'si'
        
        ultimo_numero = Factura.query.order_by(Factura.id.desc()).first()
        if ultimo_numero:
            try:
                ultimo_num = int(ultimo_numero.numero_factura.split('-')[-1])
                nuevo_numero = f"FACE-{datetime.now().year}-{(ultimo_num + 1):04d}"
            except:
                nuevo_numero = f"FACE-{datetime.now().year}-{(ultimo_numero.id + 1):04d}"
        else:
            nuevo_numero = f"FACE-{datetime.now().year}-0001"
        
        subtotal = reserva.total_pago
        impuesto = 0
        total = subtotal
        
        factura = Factura(
            reservacion_id=reserva.id,
            numero_factura=nuevo_numero,
            subtotal=subtotal,
            impuesto=impuesto,
            total=total,
            nombre_cliente=reserva.nombre_huesped,
            nit_cliente=reserva.cedula_nit,
            tipo_documento=reserva.tipo_documento,
            direccion_cliente=direccion,
            metodo_pago=metodo_pago,
            estado='pagada',
            email_cliente=reserva.email_huesped
        )
        db.session.add(factura)
        db.session.flush()
        
        reserva.estado = 'facturada'
        
        # Enviar email si se pidió
        if enviar_email and reserva.email_huesped:
            config = ConfigHotel.query.first()
            habitacion = reserva.habitacion
            from app.routes.facturacion import enviar_factura_email
            try:
                email_enviado = enviar_factura_email(factura, reserva, habitacion, config)
                if email_enviado:
                    factura.correo_enviado = True
            except:
                pass
        
        db.session.commit()
    
        flash(f'Factura {nuevo_numero} generada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('reportes.lista_facturas'))

@reportes_bp.route('/factura_gen/<int:reservacion_id>')
@login_required
def generar_factura_get(reservacion_id):
    reserva = Reservacion.query.get_or_404(reservacion_id)
    habitacion = reserva.habitacion
    config = ConfigHotel.query.first()
    consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).all()
    costo_noches = reserva.total_pago - sum(c.monto for c in consumos)
    return render_template('reportes/factura_generar.html', 
                        reserva=reserva, habitacion=habitacion, config=config,
                        consumos=consumos, costo_noches=costo_noches)

@reportes_bp.route('/config_hotel', methods=['GET', 'POST'])
@admin_required
def config_hotel():
    config = ConfigHotel.query.first()
    if not config:
        config = ConfigHotel()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.nit = request.form.get('nit')
        config.nombre = request.form.get('nombre')
        config.direccion = request.form.get('direccion')
        config.ciudad = request.form.get('ciudad')
        config.telefono = request.form.get('telefono')
        config.email = request.form.get('email')
        config.web = request.form.get('web')
        db.session.commit()
        flash('Configuración del hotel actualizada.', 'success')
        return redirect(url_for('reportes.config_hotel'))
    
    return render_template('reportes/config_hotel.html', config=config)

@reportes_bp.route('/imprimir_factura/<int:factura_id>')
@login_required
def imprimir_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    reserva = Reservacion.query.get(factura.reservacion_id)
    habitacion = Habitacion.query.get(reserva.habitacion_id)
    consumos = ConsumoPOS.query.filter_by(reservacion_id=reserva.id).all()
    
    total_extras = sum(c.monto for c in consumos)
    costo_noches = reserva.total_pago - total_extras
    
    config = ConfigHotel.query.first()
    if not config:
        config = ConfigHotel()
        db.session.add(config)
        db.session.commit()
    
    return render_template('reportes/factura_imprimir.html',
                          reserva=reserva,
                          habitacion=habitacion,
                          consumos=consumos,
                          costo_noches=costo_noches,
                          total_extras=total_extras,
                          config=config,
                          factura=factura)

@reportes_bp.route('/facturas')
@admin_required
def lista_facturas():
    facturas = Factura.query.order_by(Factura.fecha_emision.desc()).all()
    return render_template('reportes/lista_facturas.html', facturas=facturas)

@reportes_bp.route('/facturas/reenviar/<int:factura_id>')
@admin_required
def reenviar_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    reserva = Reservacion.query.get(factura.reservacion_id)
    habitacion = Habitacion.query.get(reserva.habitacion_id)
    config = ConfigHotel.query.first()
    
    if reserva.email_huesped:
        email_enviado = enviar_factura_email(factura, reserva, habitacion, config)
        if email_enviado:
            factura.correo_enviado = True
            db.session.commit()
            flash(f'Factura enviada a {reserva.email_huesped}', 'success')
        else:
            flash('Error al enviar el correo. Verifique que el email sea válido.', 'danger')
    else:
        flash('La reserva no tiene email registrado.', 'warning')
    
    return redirect(url_for('reportes.lista_facturas'))

@reportes_bp.route('/clientes')
@admin_required
def lista_clientes():
    clientes = ClienteFactura.query.order_by(ClienteFactura.nombre).all()
    return render_template('reportes/clientes.html', clientes=clientes)

@reportes_bp.route('/clientes/guardar', methods=['POST'])
@admin_required
def guardar_cliente():
    nit = request.form.get('nit', '').strip()
    nombre = request.form.get('nombre', '').strip()
    tipo_documento = request.form.get('tipo_documento', 'nit')
    direccion = request.form.get('direccion', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    
    if not nit or not nombre:
        flash('NIT y nombre son obligatorios.', 'danger')
        return redirect(url_for('reportes.lista_clientes'))
    
    # Check if exists
    cliente_existente = ClienteFactura.query.filter_by(nit=nit).first()
    if cliente_existente:
        cliente_existente.nombre = nombre
        cliente_existente.tipo_documento = tipo_documento
        cliente_existente.direccion = direccion
        cliente_existente.email = email
        cliente_existente.telefono = telefono
        flash(f'Cliente {nombre} actualizado.', 'success')
    else:
        nuevo_cliente = ClienteFactura(
            nit=nit,
            nombre=nombre,
            tipo_documento=tipo_documento,
            direccion=direccion,
            email=email,
            telefono=telefono
        )
        db.session.add(nuevo_cliente)
        flash(f'Cliente {nombre} registrado.', 'success')
    
    db.session.commit()
    return redirect(url_for('reportes.lista_clientes'))

@reportes_bp.route('/clientes/buscar/<nit>')
@empleado_required
def buscar_cliente(nit):
    cliente = ClienteFactura.query.filter_by(nit=nit).first()
    if cliente:
        return jsonify({
            'encontrado': True,
            'nit': cliente.nit,
            'nombre': cliente.nombre,
            'tipo_documento': cliente.tipo_documento,
            'direccion': cliente.direccion or '',
            'email': cliente.email or '',
            'telefono': cliente.telefono or ''
        })
    return jsonify({'encontrado': False})
"""
Panel de Empleado - Blueprint con RBAC
Acceso: Solo empleados (NO admins)
Funciones: Reservas, Facturación, Consumos, Clientes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Habitacion, Reservacion, ConsumoPOS, HorarioEmpleado, Empleado, Factura, ClienteFactura, User, ConfigHotel
from app import db
from datetime import datetime, timezone
from flask_login import login_required, current_user, logout_user
from app.helpers.rbac import empleado_required

empleado_bp = Blueprint('empleado', __name__, url_prefix='/empleado')


@empleado_bp.route('/')
def index():
    """Redirige al dashboard según rol"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if getattr(current_user, 'rol', None) == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('empleado.dashboard'))


@empleado_bp.route('/dashboard')
@login_required
@empleado_required
def dashboard():
    """Dashboard del empleado"""
    from app.models import Reservacion
    from datetime import datetime
    
    hoy = datetime.now().date()
    
    libres = Habitacion.query.filter_by(estado='Disponible').count()
    ocupadas = Habitacion.query.filter_by(estado='Ocupada').count()
    
    # Check-ins hoy
    checkins_hoy = Reservacion.query.filter(
        Reservacion.fecha_inicio == hoy,
        Reservacion.estado == 'activa'
    ).count()
    
    # Check-outs hoy
    checkouts_hoy = Reservacion.query.filter(
        Reservacion.fecha_fin == hoy,
        Reservacion.estado == 'checkin'
    ).count()
    
    pendientes_pago = 0
    for hab in Habitacion.query.filter_by(estado='Ocupada').all():
        reserva = Reservacion.query.filter_by(habitacion_id=hab.id).order_by(Reservacion.id.desc()).first()
        if reserva and not reserva.pagado:
            pendientes_pago += 1
    
    # Obtener datos de horario del empleado
    hora_entrada = None
    hora_salida = None
    horas_trabajadas = None
    
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if empleado:
        hora_entrada = empleado.hora_entrada
        hora_salida = empleado.hora_salida
        horas_trabajadas = empleado.horas_trabajadas()
    
    return render_template('empleado/dashboard.html',
                         libres=libres,
                         ocupadas=ocupadas,
                         checkins_hoy=checkins_hoy,
                         checkouts_hoy=checkouts_hoy,
                         pendientes=pendientes_pago,
                         hora_entrada=hora_entrada,
                         hora_salida=hora_salida,
                         horas_trabajadas=horas_trabajadas)


@empleado_bp.route('/registrar_entrada', methods=['POST'])
@login_required
@empleado_required
def registrar_entrada():
    """Registrar hora de entrada"""
    from datetime import datetime
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if empleado:
        empleado.hora_entrada = datetime.now()
        db.session.commit()
        flash('Entrada registrada. ¡Buen turno!', 'success')
    return redirect(url_for('empleado.dashboard'))


@empleado_bp.route('/registrar_salida', methods=['POST'])
@login_required
@empleado_required
def registrar_salida():
    """Registrar hora de salida"""
    from datetime import datetime
    empleado = Empleado.query.filter_by(user_id=current_user.id).first()
    if empleado:
        empleado.hora_salida = datetime.now()
        db.session.commit()
        flash('Salida registrada. ¡Hasta mañana!', 'success')
    return redirect(url_for('empleado.dashboard'))


@empleado_bp.route('/logout')
@login_required
@empleado_required
def logout():
    """Cerrar sesión"""
    logout_user()
    return redirect(url_for('auth.login'))


# ============================================
# RECEPCIÓN - Reservar habitaciones
# ============================================

@empleado_bp.route('/recepcion')
@login_required
@empleado_required
def recepcion():
    """Panel de recepción"""
    habitaciones_libres = Habitacion.query.filter_by(estado='Disponible').order_by(Habitacion.numero).all()
    habitaciones_mantenimiento = Habitacion.query.filter_by(estado='Mantenimiento').order_by(Habitacion.numero).all()
    habitaciones_ocupadas = Habitacion.query.filter_by(estado='Ocupada').all()
    
    pendientes = []
    pagadas = []
    
    for hab in habitaciones_ocupadas:
        reserva = Reservacion.query.filter_by(habitacion_id=hab.id).order_by(Reservacion.id.desc()).first()
        if reserva:
            item = {'habitacion': hab, 'reserva': reserva}
            if reserva.pagado:
                pagadas.append(item)
            else:
                pendientes.append(item)
    
    return render_template('empleado/recepcion.html',
                         libres=habitaciones_libres,
                         mantenimiento=habitaciones_mantenimiento,
                         pendientes=pendientes,
                         pagadas=pagadas)


@empleado_bp.route('/reserva/nueva/<int:habitacion_id>', methods=['GET', 'POST'])
@login_required
@empleado_required
def nueva_reserva(habitacion_id):
    """Crear nueva reserva"""
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    
    if habitacion.estado == 'Mantenimiento':
        flash('Esta habitación está bajo mantenimiento y no puede reservarse por ahora.', 'warning')
        return redirect(url_for('empleado.recepcion'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email_cliente = request.form.get('email_huesped', '').strip()
        fecha_inicio = request.form.get('fecha_ingreso', '')
        fecha_fin = request.form.get('fecha_salida', '')
        tipo_doc = request.form.get('tipo_documento', 'cedula')
        cedula = request.form.get('cedula', '').strip()
        
        hay_menores = request.form.get('hay_menores', 'no') == 'si'
        cantidad_menores = int(request.form.get('cantidad_menores', 0)) if hay_menores else 0
        
        lista_menores = []
        if hay_menores:
            for i in range(1, cantidad_menores + 1):
                m_nombre = request.form.get(f'nombre_menor_{i}', '').strip()
                m_doc = request.form.get(f'doc_menor_{i}', '').strip()
                if m_nombre:
                    lista_menores.append({
                        'nombre': m_nombre,
                        'documento': m_doc
                    })
        
        try:
            fecha_in = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_out = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            dias = (fecha_out - fecha_in).days
            
            if dias <= 0:
                flash('La fecha de salida debe ser mayor.', 'warning')
                return render_template('empleado/reserva_form.html', habitacion=habitacion)
            
            datos_menores_json = ''
            if lista_menores:
                import json
                datos_menores_json = json.dumps(lista_menores)
            
            reserva = Reservacion(
                habitacion_id=habitacion_id,
                nombre_cliente=nombre,
                telefono_cliente=telefono,
                email_cliente=email_cliente,
                tipo_documento=tipo_doc,
                cedula_nit=cedula,
                fecha_inicio=fecha_in,
                fecha_fin=fecha_out,
                total_pago=dias * habitacion.precio_noche,
                estado='activa',
                menores=len(lista_menores),
                datos_menores=datos_menores_json if lista_menores else None,
                empleado_id=current_user.id,
                codigo=Reservacion.generar_codigo()
            )
            db.session.add(reserva)
            habitacion.estado = 'Ocupada'
            db.session.commit()
            
            flash(f'Reserva creada para {nombre}. Liquidación se gestionará en Caja.', 'success')
            return redirect(url_for('empleado.recepcion'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('empleado/reserva_form.html', habitacion=habitacion)


@empleado_bp.route('/reserva/<int:reserva_id>/accion', methods=['POST'])
@login_required
@empleado_required
def accion_reserva(reserva_id):
    """Acciones: checkin, checkout, pagar"""
    reserva = Reservacion.query.get_or_404(reserva_id)
    accion = request.form.get('accion')
    
    if accion == 'checkin':
        reserva.estado = 'checkin'
        reserva.fecha_checkin = datetime.now()
        flash(f'Check-in exitoso para {reserva.nombre_cliente}. ¡Bienvenidos!', 'success')
        return redirect(url_for('empleado.recepcion'))

    elif accion == 'checkout':
        reserva.estado = 'completada'
        reserva.fecha_checkout = datetime.now()
        # Al salir el huésped, la habitación queda disponible inmediatamente
        habitacion = Habitacion.query.get(reserva.habitacion_id)
        if habitacion:
            habitacion.estado = 'Disponible'
        
        db.session.commit()
        flash(f'Check-out de {reserva.nombre_cliente} completado. La Habitación #{habitacion.numero} ahora está disponible.', 'success')
        return redirect(url_for('empleado.recepcion'))

    elif accion == 'pagar':
        reserva.pagado = True
        
        # Generar factura electrónica automáticamente
        from app.routes.reportes import generar_factura_automatica
        try:
            factura = generar_factura_automatica(reserva)
            if factura:
                db.session.commit()
                flash(f'Pago registrado y factura {factura.numero_factura} generada.', 'success')
                return redirect(url_for('reportes.imprimir_factura', factura_id=factura.id))
            else:
                db.session.commit()
                flash('Pago registrado. No se pudo generar factura automáticamente.', 'warning')
        except Exception as e:
            print(f"ERROR al generar factura: {e}")
            db.session.commit()
            flash(f'Pago registrado pero error al generar factura: {e}', 'warning')
        
        return redirect(url_for('empleado.recepcion'))
    
    db.session.commit()
    return redirect(url_for('empleado.recepcion'))


@empleado_bp.route('/habitacion/<int:habitacion_id>/mantenimiento', methods=['POST'])
@login_required
@empleado_required
def toggle_mantenimiento(habitacion_id):
    """Poner o quitar habitación de mantenimiento"""
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    if habitacion.estado == 'Disponible':
        habitacion.estado = 'Mantenimiento'
        flash(f'Habitación {habitacion.numero} puesta en mantenimiento.', 'warning')
    elif habitacion.estado == 'Mantenimiento':
        habitacion.estado = 'Disponible'
        flash(f'Habitación {habitacion.numero} ahora está disponible.', 'success')
    else:
        flash('Solo se pueden poner en mantenimiento habitaciones que estén disponibles.', 'danger')
    
    db.session.commit()
    return redirect(url_for('empleado.recepcion'))

@empleado_bp.route('/habitacion/estado/<int:habitacion_id>', methods=['POST'])
@login_required
@empleado_required
def cambiar_estado_habitacion(habitacion_id):
    """Cambiar estado de habitación directamente"""
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado in ['Disponible', 'Ocupada', 'Mantenimiento']:
        habitacion.estado = nuevo_estado
        db.session.commit()
        flash(f'Habitación {habitacion.numero} actualizada a {nuevo_estado}.', 'success')
    else:
        flash('Estado no válido.', 'danger')
    
    return redirect(url_for('empleado.recepcion'))


# ============================================
# CONSUMOS - Agregar extras a habitaciones
# ============================================

@empleado_bp.route('/consumos')
@login_required
@empleado_required
def consumos():
    """Panel de consumos"""
    activas = []
    for hab in Habitacion.query.filter_by(estado='Ocupada').all():
        reserva = Reservacion.query.filter_by(habitacion_id=hab.id).order_by(Reservacion.id.desc()).first()
        if reserva:
            activas.append({
                'habitacion': hab,
                'reserva': reserva,
                'reserva_id': reserva.id
            })
    
    return render_template('empleado/consumos.html', activas=activas)


@empleado_bp.route('/consumo/agregar/<int:reserva_id>', methods=['POST'])
@login_required
@empleado_required
def agregar_consumo(reserva_id):
    """Agregar consumo extra"""
    producto = request.form.get('producto', '').strip()
    monto = request.form.get('monto', '')
    
    if not producto or not monto:
        flash('Complete todos los campos.', 'warning')
        return redirect(url_for('empleado.consumos'))
    
    try:
        consumo = ConsumoPOS(
            reservacion_id=reserva_id,
            producto=producto,
            monto=float(monto),
            empleado_id=current_user.id
        )
        db.session.add(consumo)
        db.session.commit()
        flash(f'Consumo agregado: {producto} - ${float(monto):,.0f}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('empleado.consumos'))


# ============================================
# FACTURACIÓN - Generar facturas
# ============================================

@empleado_bp.route('/facturacion')
@login_required
@empleado_required
def facturacion():
    """Panel de facturación y cobros"""
    from datetime import datetime
    reservas_activas = Reservacion.query.filter(
        Reservacion.estado.in_(['checkin', 'activa'])
    ).order_by(Reservacion.id.desc()).all()
    
    total_hoy = sum(r.total_pago for r in reservas_activas)
    
    return render_template('empleado/facturacion.html', reservas_activas=reservas_activas, total_hoy=total_hoy)


@empleado_bp.route('/cobrar/<int:reserva_id>', methods=['POST'])
@login_required
@empleado_required
def cobrar_reserva(reserva_id):
    """Cobrar una reserva y generar factura"""
    try:
        reserva = Reservacion.query.get_or_404(reserva_id)
        reserva_id_value = reserva.id
        nombre_cliente = reserva.nombre_cliente
        email_cliente = reserva.email_cliente
        total_pago = reserva.total_pago
    except Exception as e:
        flash(f'Error: Reserva no encontrada', 'danger')
        return redirect(url_for('empleado.facturacion'))
    
    factura_electronica = request.form.get('factura_electronica') == 'si'
    imprimir = request.form.get('imprimir') == 'si'
    
    reserva.pagado = True
    reserva.estado = 'facturada'
    
    # Generar número de factura
    ultimo = Factura.query.order_by(Factura.id.desc()).first()
    from datetime import datetime
    year = datetime.now().year
    if ultimo:
        try:
            num = int(ultimo.numero_factura.split('-')[-1]) + 1
            nuevo_num = f"FACE-{year}-{num:04d}"
        except:
            nuevo_num = f"FACE-{year}-{Factura.query.count() + 1:04d}"
    else:
        nuevo_num = f"FACE-{year}-0001"
    
    factura = Factura(
        reservacion_id=reserva.id,
        numero_factura=nuevo_num,
        subtotal=reserva.total_pago,
        impuesto=0,
        total=reserva.total_pago,
        nombre_cliente=reserva.nombre_cliente,
        nit_cliente=reserva.cedula_nit,
        tipo_documento=reserva.tipo_documento,
        metodo_pago='Efectivo',
        estado='pagada'
    )
    db.session.add(factura)
    db.session.commit()
    
    # Enviar correo si aplica
    correo_enviado = False
    msg_factura = ''
    
    if factura_electronica and email_cliente:
        try:
            from app.services.email_service import EmailService
            habitacion = Habitacion.query.get(reserva.habitacion_id)
            config = ConfigHotel.query.first()
            print(f"[DEBUG] Email: {email_cliente}")
            print(f"[DEBUG] Habitacion: {habitacion}")
            print(f"[DEBUG] Config: {config}")
            if habitacion and config:
                correo_enviado = EmailService.enviar_factura(factura, reserva, habitacion, config)
                print(f"[DEBUG] Correo enviado: {correo_enviado}")
            else:
                print("[DEBUG] Faltan habitacion o config")
        except Exception as e:
            print(f"[ERROR] Enviando correo: {e}")
            import traceback
            traceback.print_exc()
    
    # Mensaje según resultado
    if correo_enviado:
        msg_factura = f' Factura {nuevo_num} enviada al correo.'
    elif factura_electronica:
        msg_factura = f' Factura {nuevo_num} generada.'
    
    flash(f'¡Gracias por su pago!{msg_factura}', 'success')
    
    # Redirigir según elección
    if imprimir and (factura_electronica or not factura_electronica):
        return redirect(url_for('empleado.imprimir_factura', factura_id=factura.id))
    
    return redirect(url_for('empleado.facturacion'))


@empleado_bp.route('/factura/imprimir/<int:factura_id>')
@login_required
@empleado_required
def imprimir_factura(factura_id):
    """Mostrar factura para imprimir"""
    factura = Factura.query.get_or_404(factura_id)
    reserva = Reservacion.query.get(factura.reservacion_id)
    habitacion = Habitacion.query.get(reserva.habitacion_id) if reserva else None
    config = ConfigHotel.query.first()
    
    return render_template('empleado/factura_imprimir.html',
                         factura=factura, reserva=reserva, habitacion=habitacion, config=config)



@empleado_bp.route('/facturas')
@login_required
@empleado_required
def lista_facturas():
    """Lista de facturas"""
    buscar = request.args.get('buscar', '')
    query = Factura.query
    if buscar:
        query = query.filter(
            (Factura.numero_factura.ilike(f'%{buscar}%')) | 
            (Factura.nombre_cliente.ilike(f'%{buscar}%'))
    )
    facturas = query.order_by(Factura.fecha_emision.desc()).limit(100).all()
    return render_template('empleado/facturas.html', facturas=facturas, buscar=buscar)


@empleado_bp.route('/factura/enviar/<int:factura_id>', methods=['POST'])
@login_required
@empleado_required
def enviar_factura(factura_id):
    """Reenviar factura por correo"""
    factura = Factura.query.get_or_404(factura_id)
    reserva = Reservacion.query.get(factura.reservacion_id)
    habitacion = db.session.get(Habitacion, reserva.habitacion_id) if reserva else None
    config = ConfigHotel.query.first()
    
    if not reserva or not reserva.email_cliente:
        flash('La reserva no tiene email registrado', 'danger')
        return redirect(url_for('empleado.lista_facturas'))
    
    try:
        from app.services.email_service import EmailService
        resultado = EmailService.enviar_factura(factura, reserva, habitacion, config)
        if resultado:
            flash(f'Factura reenviada a {reserva.email_cliente}', 'success')
        else:
            flash('No se pudo enviar el correo. Verifique la configuración SMTP.', 'danger')
    except Exception as e:
        flash(f'Error al enviar: {e}', 'danger')
    
    return redirect(url_for('empleado.lista_facturas'))


# ============================================
# CLIENTES - Gestión de clientes para facturación
# ============================================

@empleado_bp.route('/clientes')
@login_required
@empleado_required
def lista_clientes():
    """Lista de clientes"""
    buscar = request.args.get('buscar', '')
    query = ClienteFactura.query
    if buscar:
        query = query.filter(
            db.or_(
                ClienteFactura.nombre.ilike(f'%{buscar}%'),
                ClienteFactura.nit.ilike(f'%{buscar}%')
            )
        )
    clientes = query.order_by(ClienteFactura.nombre).limit(100).all()
    return render_template('empleado/clientes.html', clientes=clientes, buscar=buscar)


@empleado_bp.route('/cliente/nuevo', methods=['GET', 'POST'])
@login_required
@empleado_required
def nuevo_cliente():
    """Agregar cliente"""
    if request.method == 'POST':
        try:
            nit = request.form.get('nit', '').strip()
            nombre = request.form.get('nombre', '').strip()
            tipo_doc = request.form.get('tipo_documento', 'nit')
            direccion = request.form.get('direccion', '').strip()
            email = request.form.get('email', '').strip()
            telefono = request.form.get('telefono', '').strip()
            
            if not nit or not nombre:
                flash('NIT y Nombre son obligatorios.', 'warning')
                return render_template('empleado/cliente_form.html')
            
            existente = ClienteFactura.query.filter_by(nit=nit).first()
            if existente:
                flash('Ya existe un cliente con este NIT.', 'warning')
                return render_template('empleado/cliente_form.html')
            
            cliente = ClienteFactura(
                nit=nit,
                nombre=nombre,
                tipo_documento=tipo_doc,
                direccion=direccion,
                email=email,
                telefono=telefono
            )
            db.session.add(cliente)
            db.session.commit()
            flash(f'Cliente {nombre} agregado.', 'success')
            return redirect(url_for('empleado.lista_clientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('empleado/cliente_form.html')
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Habitacion, User, Empleado, ConsumoPOS, TurnoEmpleado
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from app.helpers.rbac import admin_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'habitaciones')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

admin_bp = Blueprint('admin', __name__)



@admin_bp.route('/')
@admin_required
def dashboard():
    """Dashboard administrativo"""
    from datetime import datetime
    from app.models import Empleado, TurnoEmpleado
    from sqlalchemy import or_
    
    habitaciones = Habitacion.query.all()
    usuarios = User.query.all()
    hoy = datetime.now().date()
    
    # Todos los turnos de hoy
    turnos_hoy = []
    for turno in TurnoEmpleado.query.filter_by(fecha=hoy).order_by(TurnoEmpleado.hora_entrada.desc()).all():
        emp = db.session.get(Empleado, turno.empleado_id)
        if emp:
            horas = turno.horas if turno.horas else (turno.calcular_horas() if turno.hora_entrada else 0)
            entrada_str = turno.hora_entrada.strftime('%H:%M') if turno.hora_entrada else '-'
            salida_str = turno.hora_salida.strftime('%H:%M') if turno.hora_salida else 'En turno'
            
            turnos_hoy.append({
                'nombre': emp.nombre,
                'cargo': emp.cargo,
                'entrada': entrada_str,
                'salida': salida_str,
                'horas': horas,
                'estado': turno.estado
            })
    
    print(f"[DEBUG] Turnos hoy: {len(turnos_hoy)}")
    for t in turnos_hoy:
        print(f"[DEBUG]   {t}")
    
    # Empleados actualmente en turno (sin salida)
    empleados_en_turno = []
    for emp in Empleado.query.filter_by(activo=True).all():
        if emp.user_id:
            tiene_turno_hoy = TurnoEmpleado.query.filter_by(
                empleado_id=emp.id,
                fecha=hoy,
                hora_salida=None
            ).first()
            if tiene_turno_hoy:
                horas = tiene_turno_hoy.calcular_horas()
                empleados_en_turno.append({
                    'nombre': emp.nombre,
                    'cargo': emp.cargo,
                    'entrada': tiene_turno_hoy.hora_entrada.strftime('%H:%M') if tiene_turno_hoy.hora_entrada else '-',
                    'horas': horas,
                    'estado': 'En turno'
                })
    
    return render_template('admin/dashboard.html', 
                         habitaciones=habitaciones,
                         usuarios=usuarios,
                         empleados_en_turno=empleados_en_turno,
                         turnos_hoy=turnos_hoy)

@admin_bp.route('/habitaciones')
@admin_required
def gestionar_habitaciones():
    habitaciones = Habitacion.query.order_by(Habitacion.numero).all()
    return render_template('admin/habitaciones.html', habitaciones=habitaciones)

@admin_bp.route('/habitaciones/nueva', methods=['GET', 'POST'])
@admin_required
def nueva_habitacion():
    if request.method == 'POST':
        try:
            imagen_filename = None
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and allowed_file(file.filename):
                    imagen_filename = secure_filename(file.filename)
                    upload_path = os.path.join(UPLOAD_FOLDER, imagen_filename)
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    file.save(upload_path)
            
            habitacion = Habitacion(
                numero=request.form.get('numero'),
                tipo=request.form.get('tipo'),
                precio_noche=float(request.form.get('precio_noche')),
                descripcion=request.form.get('descripcion'),
                cantidad_camas=int(request.form.get('cantidad_camas', 1)),
                tipo_camas=request.form.get('tipo_camas'),
                tiene_bano_privado='tiene_bano_privado' in request.form,
                tiene_ventana='tiene_ventana' in request.form,
                tiene_terraza='tiene_terraza' in request.form,
                tiene_frigobar='tiene_frigobar' in request.form,
                tiene_aire='tiene_aire' in request.form,
                tiene_television='tiene_television' in request.form,
                wifi='wifi' in request.form,
                capacidad_max=int(request.form.get('capacidad_max', 2)),
                imagen=imagen_filename
            )
            db.session.add(habitacion)
            db.session.commit()
            flash('Habitación creada exitosamente.', 'success')
            return redirect(url_for('admin.gestionar_habitaciones'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/form_habitacion.html', habitacion=None)

@admin_bp.route('/habitaciones/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_habitacion(id):
    habitacion = Habitacion.query.get_or_404(id)
    if request.method == 'POST':
        try:
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and allowed_file(file.filename):
                    imagen_filename = secure_filename(file.filename)
                    upload_path = os.path.join(UPLOAD_FOLDER, imagen_filename)
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    file.save(upload_path)
                    habitacion.imagen = imagen_filename
            
            habitacion.numero = request.form.get('numero')
            habitacion.tipo = request.form.get('tipo')
            habitacion.precio_noche = float(request.form.get('precio_noche'))
            habitacion.descripcion = request.form.get('descripcion')
            habitacion.cantidad_camas = int(request.form.get('cantidad_camas', 1))
            habitacion.tipo_camas = request.form.get('tipo_camas')
            habitacion.tiene_bano_privado = 'tiene_bano_privado' in request.form
            habitacion.tiene_ventana = 'tiene_ventana' in request.form
            habitacion.tiene_terraza = 'tiene_terraza' in request.form
            habitacion.tiene_frigobar = 'tiene_frigobar' in request.form
            habitacion.tiene_aire = 'tiene_aire' in request.form
            habitacion.tiene_television = 'tiene_television' in request.form
            habitacion.wifi = 'wifi' in request.form
            habitacion.capacidad_max = int(request.form.get('capacidad_max', 2))
            db.session.commit()
            flash('Habitación actualizada.', 'success')
            return redirect(url_for('admin.gestionar_habitaciones'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/form_habitacion.html', habitacion=habitacion)

@admin_bp.route('/habitaciones/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_habitacion(id):
    habitacion = Habitacion.query.get_or_404(id)
    if habitacion.estado == 'Ocupada':
        flash('No se puede eliminar una habitación ocupada.', 'warning')
        return redirect(url_for('admin.gestionar_habitaciones'))
    try:
        db.session.delete(habitacion)
        db.session.commit()
        flash('Habitación eliminada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_habitaciones'))

@admin_bp.route('/usuarios')
@admin_required
def gestionar_usuarios():
    usuarios = User.query.order_by(User.nombre).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_usuario():
    if request.method == 'POST':
        try:
            if User.query.filter_by(username=request.form.get('username')).first():
                flash('El usuario ya existe.', 'danger')
                return redirect(url_for('admin.nuevo_usuario'))
            
            usuario = User(
                username=request.form.get('username'),
                password=request.form.get('password'),
                nombre=request.form.get('nombre'),
                email=request.form.get('email'),
                telefono=request.form.get('telefono'),
                rol=request.form.get('rol')
            )
            db.session.add(usuario)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('admin.gestionar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/form_usuario.html', usuario=None)

@admin_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_usuario(id):
    usuario = User.query.get_or_404(id)
    if request.method == 'POST':
        try:
            usuario.nombre = request.form.get('nombre')
            usuario.email = request.form.get('email')
            usuario.telefono = request.form.get('telefono')
            usuario.rol = request.form.get('rol')
            if request.form.get('password'):
                usuario.password = request.form.get('password')
            db.session.commit()
            flash('Usuario actualizado.', 'success')
            return redirect(url_for('admin.gestionar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/form_usuario.html', usuario=usuario)

@admin_bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_usuario(id):
    usuario = User.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'warning')
        return redirect(url_for('admin.gestionar_usuarios'))
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/usuarios/toggle/<int:id>')
@admin_required
def toggle_usuario(id):
    usuario = User.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No puedes desactivarte a ti mismo.', 'warning')
        return redirect(url_for('admin.gestionar_usuarios'))
    usuario.activo = not usuario.activo
    db.session.commit()
    estado = 'activado' if usuario.activo else 'desactivado'
    flash(f'Usuario {estado}.', 'success')
    return redirect(url_for('admin.gestionar_usuarios'))

@admin_bp.route('/empleados')
@admin_required
def gestionar_empleados():
    empleados = Empleado.query.order_by(Empleado.nombre).all()
    
    # Obtener usuarios para mostrar
    usuarios = {u.id: u.username for u in User.query.all()}
    
    return render_template('admin/empleados.html', empleados=empleados, usuarios=usuarios)

@admin_bp.route('/empleados/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_empleado():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        cargo = request.form.get('cargo', 'Empleado')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not nombre:
            flash('El nombre es obligatorio.', 'warning')
            return redirect(url_for('admin.nuevo_empleado'))
        
        if not username or not password:
            flash('El usuario y contraseña son obligatorios.', 'warning')
            return redirect(url_for('admin.nuevo_empleado'))
        
        existente = User.query.filter_by(username=username).first()
        if existente:
            flash(f'El usuario "{username}" ya existe.', 'warning')
            return redirect(url_for('admin.nuevo_empleado'))
        
        try:
            user = User(
                username=username,
                nombre=nombre,
                email=email,
                telefono=telefono,
                rol=cargo.lower(),
                activo=True
            )
            user.password = password
            db.session.add(user)
            db.session.flush()
            
            empleado = Empleado(
                nombre=nombre,
                telefono=telefono,
                email=email,
                cargo=cargo,
                user_id=user.id
            )
            db.session.add(empleado)
            db.session.commit()
            
            flash(f'Empleado {nombre} agregado con usuario: {username}', 'success')
            return redirect(url_for('admin.gestionar_empleados'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/form_empleado.html')

@admin_bp.route('/empleados/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    user = User.query.get(empleado.user_id) if empleado.user_id else None
    
    if request.method == 'POST':
        empleado.nombre = request.form.get('nombre')
        empleado.telefono = request.form.get('telefono')
        empleado.email = request.form.get('email')
        empleado.cargo = request.form.get('cargo', 'Empleado')
        
        nueva_pass = request.form.get('password')
        if nueva_pass and user:
            user.password = nueva_pass
        
        try:
            db.session.commit()
            flash('Empleado actualizado.', 'success')
            return redirect(url_for('admin.gestionar_empleados'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/form_empleado.html', empleado=empleado)

@admin_bp.route('/empleados/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    nombre = empleado.nombre
    try:
        db.session.delete(empleado)
        db.session.commit()
        flash(f'Empleado {nombre} eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.gestionar_empleados'))

@admin_bp.route('/empleados/reportes')
@admin_required
def reportes_empleados():
    hoy = datetime.now().date()
    
    desde_diario = datetime.combine(hoy, datetime.min.time())
    hasta_diario = datetime.combine(hoy, datetime.max.time())
    
    desde_quincenal = datetime.combine(hoy.replace(day=1), datetime.min.time())
    hasta_quincenal = datetime.combine(hoy.replace(day=15 if hoy.day <= 15 else 1) + timedelta(days=1 if hoy.day > 15 else 0), datetime.min.time()) if hoy.day > 15 else datetime.combine(hoy, datetime.max.time())
    
    desde_mensual = datetime.combine(hoy.replace(day=1), datetime.min.time())
    hasta_mensual = datetime.combine(hoy.replace(day=1) + timedelta(days=32), datetime.min.time())
    
    empleados = Empleado.query.filter_by(activo=True).all()
    
    ventas_empleados = []
    for emp in empleados:
        diario = db.session.query(func.sum(ConsumoPOS.monto)).filter(
            ConsumoPOS.empleado_id == emp.id,
            ConsumoPOS.fecha >= desde_diario,
            ConsumoPOS.fecha <= hasta_diario
        ).scalar() or 0
        
        quincenal = db.session.query(func.sum(ConsumoPOS.monto)).filter(
            ConsumoPOS.empleado_id == emp.id,
            ConsumoPOS.fecha >= desde_quincenal,
            ConsumoPOS.fecha <= hasta_quincenal
        ).scalar() or 0
        
        mensual = db.session.query(func.sum(ConsumoPOS.monto)).filter(
            ConsumoPOS.empleado_id == emp.id,
            ConsumoPOS.fecha >= desde_mensual,
            ConsumoPOS.fecha <= hasta_mensual
        ).scalar() or 0
        
        ventas_empleados.append({
            'empleado': emp,
            'diario': diario,
            'quincenal': quincenal,
            'mensual': mensual
        })
    
    return render_template('admin/reportes_empleados.html', ventas=ventas_empleados, hoy=hoy)

@admin_bp.route('/horarios')
@admin_required
def horarios_empleados():
    from app.models import TurnoEmpleado
    
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    horarios = TurnoEmpleado.query.join(Empleado).filter(
        TurnoEmpleado.fecha >= inicio_semana,
        TurnoEmpleado.fecha <= fin_semana
    ).order_by(TurnoEmpleado.fecha.desc(), TurnoEmpleado.hora_entrada.desc()).all()
    
    return render_template('admin/horarios.html', horarios=horarios, hoy=hoy, inicio_semana=inicio_semana, fin_semana=fin_semana)

@admin_bp.route('/horarios/iniciar', methods=['POST'])
@admin_required
def iniciar_horario():
    from app.models import TurnoEmpleado
    from datetime import datetime
    
    empleado_id = request.form.get('empleado_id')
    if not empleado_id:
        flash('Seleccione un empleado.', 'warning')
        return redirect(url_for('recep.dashboard'))
    
    hoy_date = datetime.now().date()
    ultimo = TurnoEmpleado.query.filter_by(empleado_id=empleado_id, hora_salida=None, fecha=hoy_date).first()
    if ultimo:
        flash('Este empleado ya tiene un turno activo hoy.', 'warning')
        return redirect(url_for('recep.dashboard'))
    
    now = datetime.now()
    turno = TurnoEmpleado(
        empleado_id=empleado_id, 
        fecha=hoy_date,
        hora_entrada=now,
        estado='activo'
    )
    db.session.add(turno)
    db.session.commit()
    
    flash('Turno iniciado.', 'success')
    return redirect(url_for('recep.dashboard'))

@admin_bp.route('/horarios/finalizar/<int:id>')
@admin_required
def finalizar_horario(id):
    from app.models import TurnoEmpleado
    from datetime import datetime
    
    turno = TurnoEmpleado.query.get_or_404(id)
    turno.hora_salida = datetime.now()
    turno.horas = turno.calcular_horas()
    turno.estado = 'completado'
    
    db.session.commit()
    flash('Turno finalizado.', 'success')
    return redirect(url_for('admin.horarios_empleados'))
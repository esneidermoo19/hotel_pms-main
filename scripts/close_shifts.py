from app import create_app, db
from app.models import TurnoEmpleado, Empleado
from datetime import datetime

app = create_app()
with app.app_context():
    now = datetime.now()
    
    # Cerrar turnos activos
    turnos_activos = TurnoEmpleado.query.filter_by(hora_salida=None).all()
    count = 0
    for t in turnos_activos:
        t.hora_salida = now
        t.horas = t.calcular_horas()
        t.estado = 'completado'
        count += 1
        
    # Limpiar estado en Empleado
    empleados = Empleado.query.all()
    for e in empleados:
        if e.hora_entrada and not e.hora_salida:
            e.hora_salida = now
            
    db.session.commit()
    print(f"Se cerraron exitosamente {count} turnos/sesiones activas.")

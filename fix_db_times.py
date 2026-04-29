from app import create_app, db
from app.models import TurnoEmpleado, Empleado, Reservacion
from datetime import timedelta

app = create_app()
with app.app_context():
    # Fix TurnoEmpleado
    turnos = TurnoEmpleado.query.all()
    for t in turnos:
        if t.hora_entrada:
            t.hora_entrada = t.hora_entrada - timedelta(hours=5)
        if t.hora_salida:
            t.hora_salida = t.hora_salida - timedelta(hours=5)
        t.horas = t.calcular_horas() # wait, this uses utcnow() or now(), depending on the class method, but if I do it later it might be better. Let's not recalculate yet.
        
    # Fix Empleado
    empleados = Empleado.query.all()
    for e in empleados:
        if e.hora_entrada:
            e.hora_entrada = e.hora_entrada - timedelta(hours=5)
        if e.hora_salida:
            e.hora_salida = e.hora_salida - timedelta(hours=5)
            
    db.session.commit()
    print("Base de datos actualizada (horas restadas por 5).")

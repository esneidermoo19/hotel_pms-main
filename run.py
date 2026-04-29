import sys
import os

# Verificar si el entorno virtual está activo
# (Si sys.prefix == sys.base_prefix significa que NO hay entorno activo)
if sys.prefix == getattr(sys, 'base_prefix', sys.prefix):
    print("\n" + "!"*60)
    print(" ERROR: EL ENTORNO VIRTUAL NO ESTÁ ACTIVADO ".center(60))
    print("!"*60)
    print("\nPara proteger la estabilidad del sistema, este debe ejecutarse")
    print("dentro de su entorno virtual (venv).")
    print("\nPASOS PARA ACTIVAR:")
    print("1. En la terminal escribe: .\\venv\\Scripts\\activate")
    print("2. Luego corre el programa: python run.py")
    print("!"*60 + "\n")
    sys.exit(1)

from app import create_app, db
from app.models import User, Habitacion, ConfigHotel

app = create_app()

with app.app_context():
    db.create_all()
    print("Base de datos creada: hotel.db")
    
    if not ConfigHotel.query.first():
        config = ConfigHotel(
            nombre='Hotel Boutique La Orquídea',
            nit='900.123.456-7',
            direccion='Calle 10 #5-30, Centro Histórico',
            ciudad='Bogotá D.C.',
            telefono='+57 601 234 5678',
            email='reservas@laorquidea.com',
            web='www.laorquideahotel.com'
        )
        db.session.add(config)
        print("Configuración inicial del hotel creada")

    if not User.query.filter_by(username='jhonny').first():
        jhonny = User(
            username='jhonny',
            password='6556',
            nombre='Jhonny',
            rol='admin'
        )
        db.session.add(jhonny)
        print("Usuario creado: jhonny / 6556 (admin)")
    
    if not User.query.filter_by(username='ana').first():
        ana = User(
            username='ana',
            password='1234',
            nombre='Ana Recepcionista',
            rol='recepcionista'
        )
        db.session.add(ana)
        print("Usuario creado: ana / 1234 (recepcionista)")
    
    if Habitacion.query.count() == 0:
        habitaciones = [
            Habitacion(numero='101', tipo='Simple', precio_noche=50000),
            Habitacion(numero='102', tipo='Simple', precio_noche=50000),
            Habitacion(numero='201', tipo='Doble', precio_noche=80000),
            Habitacion(numero='202', tipo='Doble', precio_noche=80000),
            Habitacion(numero='301', tipo='Suite', precio_noche=150000),
            Habitacion(numero='302', tipo='Suite', precio_noche=150000),
        ]
        db.session.add_all(habitaciones)
        print("Habitaciones de ejemplo creadas")
    
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
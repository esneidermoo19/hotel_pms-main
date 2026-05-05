import sys
import os

# Verificar si el entorno virtual está activo
# if sys.prefix == getattr(sys, 'base_prefix', sys.prefix):
#     print("\n" + "!"*60)
#     print(" ERROR: EL ENTORNO VIRTUAL NO ESTÁ ACTIVADO ".center(60))
#     print("!"*60)
#     print("\nPara proteger la estabilidad del sistema, este debe ejecutarse")
#     print("dentro de su entorno virtual (venv).")
#     print("\nPASOS PARA ACTIVAR:")
#     print("1. En la terminal escribe: .\\venv\\Scripts\\activate")
#     print("2. Luego corre el programa: python run.py")
#     print("!"*60 + "\n")
#     sys.exit(1)

from app import create_app, db
from app.models import User, Habitacion, ConfigHotel
from app.config import Config

app = create_app()

with app.app_context():
    db.create_all()
    
    # Parche para PostgreSQL: Asegurar que la columna password tenga el tamaño correcto
    if Config.SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        try:
            db.session.execute(db.text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(256)'))
            db.session.commit()
            print("Columna password actualizada a 256 caracteres en PostgreSQL")
        except Exception as e:
            db.session.rollback()
            print(f"Nota: No se pudo alterar la tabla (probablemente ya está actualizada): {e}")

    print("Base de datos verificada: hotel.db")
    
    hotel_config = ConfigHotel.query.first()
    if not hotel_config:
        hotel_config = ConfigHotel(
            nombre='Hotel Boutique La Orquídea',
            nit='900.123.456-7',
            direccion='Calle 10 #5-30, Centro Histórico',
            ciudad='Bogotá D.C.',
            telefono='+57 601 234 5678',
            email='laorquideahotel45@gmail.com',
            web='www.laorquideahotel.com'
        )
        db.session.add(hotel_config)
        print("Configuración inicial del hotel creada con correo corporativo")
    else:
        hotel_config.email = 'laorquideahotel45@gmail.com'
        print("Correo del hotel actualizado a laorquideahotel45@gmail.com")

    # Administradores
    if not User.query.filter_by(username='jhonny').first():
        jhonny = User(
            username='jhonny',
            password='6556',
            nombre='Jhonny',
            rol='admin'
        )
        db.session.add(jhonny)
        print("Usuario creado: jhonny / 6556 (admin)")

    if not User.query.filter_by(username='edwin').first():
        edwin = User(
            username='edwin',
            password='2345',
            nombre='Edwin',
            rol='admin'
        )
        db.session.add(edwin)
        print("Usuario creado: edwin / 2345 (admin)")
    
    # Recepcionistas
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
            Habitacion(
                numero='101', 
                tipo='Estándar Simple', 
                precio_noche=280000,
                descripcion='Una acogedora habitación diseñada para el descanso absoluto. Cuenta con acabados en madera noble y una iluminación cálida que invita a la relajación.',
                cantidad_camas=1,
                tipo_camas='Queen Size',
                capacidad_max=2,
                tiene_frigobar=False,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_terraza=False
            ),
            Habitacion(
                numero='102', 
                tipo='Estándar Simple', 
                precio_noche=280000,
                descripcion='Elegancia y confort en un espacio íntimo. Ideal para viajeros que buscan un refugio tranquilo en el corazón de la ciudad.',
                cantidad_camas=1,
                tipo_camas='Queen Size',
                capacidad_max=2,
                tiene_frigobar=False,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_terraza=False
            ),
            Habitacion(
                numero='201', 
                tipo='Doble Superior', 
                precio_noche=450000,
                descripcion='Espaciosa y luminosa, esta habitación ofrece vistas privilegiadas y un diseño contemporáneo. Incluye servicios premium para una estancia más completa.',
                cantidad_camas=2,
                tipo_camas='Full Size',
                capacidad_max=4,
                tiene_frigobar=True,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_ventana=True,
                tiene_terraza=False
            ),
            Habitacion(
                numero='202', 
                tipo='Doble Superior', 
                precio_noche=450000,
                descripcion='Un oasis de amplitud con detalles artesanales. Equipada con frigobar y tecnología de punta para su total comodidad.',
                cantidad_camas=2,
                tipo_camas='Full Size',
                capacidad_max=4,
                tiene_frigobar=True,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_ventana=True,
                tiene_terraza=False
            ),
            Habitacion(
                numero='301', 
                tipo='Suite Orquídea', 
                precio_noche=850000,
                descripcion='Nuestra joya de la corona. Esta suite ofrece terraza privada con vistas panorámicas, sala de estar independiente y acceso a servicios exclusivos de concierge.',
                cantidad_camas=1,
                tipo_camas='King Size Presidential',
                capacidad_max=2,
                tiene_frigobar=True,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_ventana=True,
                tiene_terraza=True
            ),
            Habitacion(
                numero='302', 
                tipo='Suite Orquídea', 
                precio_noche=850000,
                descripcion='Lujo sin precedentes. Disfrute de su terraza privada, baño con tina de hidromasaje y un sistema de sonido envolvente para una experiencia inigualable.',
                cantidad_camas=1,
                tipo_camas='King Size Presidential',
                capacidad_max=2,
                tiene_frigobar=True,
                wifi=True,
                tiene_aire=True,
                tiene_television=True,
                tiene_ventana=True,
                tiene_terraza=True
            ),
        ]
        db.session.add_all(habitaciones)
        print("Habitaciones de lujo creadas con jerarquía de beneficios")
    
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
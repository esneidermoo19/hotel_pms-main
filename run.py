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
            
        # Parche para añadir columnas nequi a config_hotel si no existen
        try:
            db.session.execute(db.text("ALTER TABLE config_hotel ADD COLUMN IF NOT EXISTS nequi_numero VARCHAR(30) DEFAULT '300 123 4567'"))
            db.session.commit()
            print("Columna nequi_numero verificada en config_hotel")
        except Exception as e:
            db.session.rollback()
             
        try:
            db.session.execute(db.text("ALTER TABLE config_hotel ADD COLUMN IF NOT EXISTS nequi_qr VARCHAR(200) DEFAULT 'img/qr_nequi.png'"))
            db.session.commit()
            print("Columna nequi_qr verificada en config_hotel")
        except Exception as e:
            db.session.rollback()
            
        # Parche para añadir columnas metodo_pago y comprobante_pago a reservacion
        for _ddl, _label in [
            ('ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS metodo_pago VARCHAR(50)', 'metodo_pago'),
            ('ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS comprobante_pago VARCHAR(255)', 'comprobante_pago'),
            # Estado del correo de confirmación (arreglo envío de correo)
            ("ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_estado VARCHAR(20) DEFAULT 'pendiente'", 'email_estado'),
            ('ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_error TEXT', 'email_error'),
            ('ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_enviado_en TIMESTAMP', 'email_enviado_en'),
            ('ALTER TABLE reservacion ADD COLUMN IF NOT EXISTS email_intentos INTEGER DEFAULT 0', 'email_intentos'),
        ]:
            try:
                db.session.execute(db.text(_ddl))
                db.session.commit()
                print(f"Columna {_label} verificada en reservacion")
            except Exception as e:
                db.session.rollback()

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
            password=Config.ADMIN_JHONNY_PASS,
            nombre='Jhonny',
            rol='admin'
        )
        db.session.add(jhonny)
        print("Usuario inicial creado: jhonny (admin)")

    if not User.query.filter_by(username='edwin').first():
        edwin = User(
            username='edwin',
            password=Config.ADMIN_EDWIN_PASS,
            nombre='Edwin',
            rol='admin'
        )
        db.session.add(edwin)
        print("Usuario inicial creado: edwin (admin)")
    
    # Recepcionistas
    if not User.query.filter_by(username='ana').first():
        ana = User(
            username='ana',
            password=Config.RECEP_ANA_PASS,
            nombre='Ana Recepcionista',
            rol='recepcionista'
        )
        db.session.add(ana)
        print("Usuario inicial creado: ana (recepcionista)")
    
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
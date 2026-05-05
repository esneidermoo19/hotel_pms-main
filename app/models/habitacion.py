from app import db

class Habitacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    tipo = db.Column(db.String(50))
    precio_noche = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.String(20), default='Disponible')
    descripcion = db.Column(db.Text)
    cantidad_camas = db.Column(db.Integer, default=1)
    tipo_camas = db.Column(db.String(50))
    tiene_bano_privado = db.Column(db.Boolean, default=True)
    tiene_ventana = db.Column(db.Boolean, default=True)
    tiene_terraza = db.Column(db.Boolean, default=False)
    tiene_frigobar = db.Column(db.Boolean, default=False)
    tiene_aire = db.Column(db.Boolean, default=True)
    tiene_television = db.Column(db.Boolean, default=True)
    wifi = db.Column(db.Boolean, default=True)
    capacidad_max = db.Column(db.Integer, default=2)
    imagen = db.Column(db.String(200))
    
    reservaciones = db.relationship('Reservacion', back_populates='habitacion')

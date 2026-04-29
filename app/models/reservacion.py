from app import db
from datetime import datetime

class Reservacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    huesped_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitacion.id'))
    fecha_ingreso = db.Column(db.DateTime, nullable=False)
    fecha_salida = db.Column(db.DateTime, nullable=False)
    total_pago = db.Column(db.Numeric(12, 2), default=0.0)
    estado = db.Column(db.String(20), default='activa')
    pagado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    
    nombre_huesped = db.Column(db.String(100), nullable=False)
    telefono_huesped = db.Column(db.String(20), nullable=False)
    email_huesped = db.Column(db.String(120))
    cedula_nit = db.Column(db.String(20), nullable=False)
    tipo_documento = db.Column(db.String(30), default='cedula')
    num_personas = db.Column(db.Integer, default=1)
    menores = db.Column(db.Integer, default=0)
    datos_menores = db.Column(db.Text)
    
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'))
    
    habitacion = db.relationship('Habitacion', back_populates='reservaciones')
    empleado = db.relationship('Empleado', backref='reservas')

from app import db
from datetime import datetime
import secrets

class Reservacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitacion.id'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    codigo = db.Column(db.String(6), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='activa')
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    
    nombre_cliente = db.Column(db.String(100), nullable=True)
    email_cliente = db.Column(db.String(120), nullable=True)
    telefono_cliente = db.Column(db.String(20), nullable=True)
    
    total_pago = db.Column(db.Numeric(12, 2), default=0.0)
    pagado = db.Column(db.Boolean, default=False)
    cedula_nit = db.Column(db.String(20), nullable=True)
    tipo_documento = db.Column(db.String(30), default='cedula')
    num_personas = db.Column(db.Integer, default=1)
    menores = db.Column(db.Integer, default=0)
    datos_menores = db.Column(db.Text)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True) # Soporte para IPv6
    metodo_pago = db.Column(db.String(50), nullable=True)
    
    habitacion = db.relationship('Habitacion', back_populates='reservaciones')
    empleado = db.relationship('Empleado', backref='reservas')
    usuario = db.relationship('User', backref='reservas')
    
    @staticmethod
    def generar_codigo():
        while True:
            codigo = secrets.token_hex(3).upper()
            if not Reservacion.query.filter_by(codigo=codigo).first():
                return codigo

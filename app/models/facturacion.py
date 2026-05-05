from app import db
from datetime import datetime

class ConsumoPOS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservacion_id = db.Column(db.Integer, db.ForeignKey('reservacion.id'))
    producto = db.Column(db.String(100))
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'))
    
    reservacion = db.relationship('Reservacion', backref='consumos_pos')
    empleado = db.relationship('Empleado', backref='ventas')

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservacion_id = db.Column(db.Integer, db.ForeignKey('reservacion.id'))
    numero_factura = db.Column(db.String(20), unique=True, nullable=False)
    fecha_emision = db.Column(db.DateTime, default=datetime.now)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    impuesto = db.Column(db.Numeric(12, 2), default=0.0)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    
    reservacion = db.relationship('Reservacion', backref='facturas')
    
    nombre_cliente = db.Column(db.String(100), nullable=False)
    nit_cliente = db.Column(db.String(20), nullable=False)
    tipo_documento = db.Column(db.String(30))
    direccion_cliente = db.Column(db.String(200))
    metodo_pago = db.Column(db.String(50), default='Efectivo')
    estado = db.Column(db.String(20), default='pagada')
    email_cliente = db.Column(db.String(120))
    pdf_url = db.Column(db.String(200))
    correo_enviado = db.Column(db.Boolean, default=False)
    xml_fel = db.Column(db.Text)
    uuid = db.Column(db.String(50))

class ClienteFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nit = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    tipo_documento = db.Column(db.String(30), default='nit')
    direccion = db.Column(db.String(200))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    


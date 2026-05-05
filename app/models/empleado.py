from app import db
from datetime import datetime

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cargo = db.Column(db.String(50), default='Empleado')
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hora_entrada = db.Column(db.DateTime, nullable=True)
    hora_salida = db.Column(db.DateTime, nullable=True)
    
    def horas_trabajadas(self):
        if self.hora_entrada and self.hora_salida:
            delta = self.hora_salida - self.hora_entrada
            return round(delta.total_seconds() / 3600, 2)
        elif self.hora_entrada:
            delta = datetime.now() - self.hora_entrada
            return round(delta.total_seconds() / 3600, 2)
        return 0
    
    def __repr__(self):
        return f'<Empleado {self.nombre}>'


class TurnoEmpleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'))
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.DateTime, nullable=True)
    hora_salida = db.Column(db.DateTime, nullable=True)
    horas = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default='activo')
    
    empleado = db.relationship('Empleado', backref='turnos')
    
    def calcular_horas(self):
        if self.hora_entrada and self.hora_salida:
            delta = self.hora_salida - self.hora_entrada
            return round(delta.total_seconds() / 3600, 2)
        elif self.hora_entrada:
            delta = datetime.now() - self.hora_entrada
            return round(delta.total_seconds() / 3600, 2)
        return 0
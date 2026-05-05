from app import db
from datetime import datetime

class HorarioEmpleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_salida = db.Column(db.DateTime)
    horas_trabajadas = db.Column(db.Float, default=0)
    
    empleado = db.relationship('Empleado', backref='horarios')
    
    def __repr__(self):
        return f'<HorarioEmpleado {self.id}>'
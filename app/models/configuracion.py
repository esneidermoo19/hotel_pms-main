from app import db

class ConfigHotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nit = db.Column(db.String(20), default='123456789-0')
    nombre = db.Column(db.String(100), default='Hotel Boutique La Orquídea')
    direccion = db.Column(db.String(200), default='Calle 10 #5-30, Centro')
    ciudad = db.Column(db.String(100), default='Bogotá D.C.')
    telefono = db.Column(db.String(20), default='+57 1 234 5678')
    email = db.Column(db.String(100), default='info@laorqui.com')
    web = db.Column(db.String(100), default='www.laorqui.com')

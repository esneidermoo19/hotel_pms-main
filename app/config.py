import os
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

class Config:
    # 1. Obtener la URI y aplicar parches de compatibilidad
    _uri = os.getenv("DATABASE_URL")
    
    if _uri:
        # Parche para Heroku/Coolify (cambiar postgres:// por postgresql://)
        if _uri.startswith("postgres://"):
            _uri = _uri.replace("postgres://", "postgresql://", 1)
        
        # Parche de seguridad: asegurar que existan las barras // después del esquema
        # Si la URI tiene ':' pero no '://', se las agregamos
        if "postgresql" in _uri and "://" not in _uri:
            _uri = _uri.replace("postgresql:", "postgresql://", 1)
        elif "postgres" in _uri and "://" not in _uri:
            _uri = _uri.replace("postgres:", "postgresql://", 1)

    # 2. Configuración de Base de Datos
    SQLALCHEMY_DATABASE_URI = _uri or 'sqlite:///hotel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 3. Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-2024-change-in-production')
    
    # 4. Configuración de Correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Hotel Boutique La Orquidea <laorquideahotel45@gmail.com>')

# Print de depuración (esto saldrá en los logs de Coolify)
# Ocultamos la contraseña por seguridad en el log real si fuera necesario, 
# pero aquí lo dejamos para verificar el formato.
print(f"DEBUG: SQLALCHEMY_DATABASE_URI procesada")

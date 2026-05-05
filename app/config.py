import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

class Config:
    # 1. Obtener la URI y aplicar parches de compatibilidad
    _uri = os.getenv("DATABASE_URL")
    
    if _uri:
        # Limpieza extrema de caracteres invisibles que Coolify podría inyectar
        _uri = _uri.strip().replace('\r', '').replace('\n', '')
        
        # Parche para Heroku/Coolify (cambiar postgres:// por postgresql://)
        if _uri.startswith("postgres://"):
            _uri = _uri.replace("postgres://", "postgresql://", 1)
        
        # Si la URI tiene el driver pero le faltan las barras, o tiene un formato raro
        # Intentamos reconstruirla asegurando el esquema postgresql://
        if "postgres" in _uri and "://" not in _uri:
            # Encontrar donde terminan las letras del esquema y empieza el usuario/contraseña
            # Buscamos el primer ':'
            match = re.search(r'([^:]+):(.*)', _uri)
            if match:
                scheme = match.group(1)
                rest = match.group(2)
                # Si el esquema no tiene 'postgresql', lo forzamos
                if "postgresql" not in scheme:
                    scheme = "postgresql"
                _uri = f"{scheme}://{rest}"

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

# Print de depuración ofuscado para ver el formato final
if Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    print(f"DEBUG URL: {Config.SQLALCHEMY_DATABASE_URI}")
else:
    # Ofuscamos: postgresql://user:pass@host -> postgresql://***:***@host
    parts = Config.SQLALCHEMY_DATABASE_URI.split('@')
    if len(parts) > 1:
        print(f"DEBUG URL FORMATO: {parts[0].split('://')[0]}://***@{(parts[1])}")
    else:
        print(f"DEBUG URL (Sin @): {Config.SQLALCHEMY_DATABASE_URI[:15]}...")

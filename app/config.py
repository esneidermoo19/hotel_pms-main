import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

class Config:
    # 1. Obtener la URI y aplicar parches de compatibilidad
    _uri = os.getenv("DATABASE_URL")
    
    if _uri:
        # Limpieza de espacios y saltos de línea
        _uri = _uri.strip().replace('\r', '').replace('\n', '')
        
        # Corregir esquema si falta // o es el formato antiguo de postgres://
        if "postgres" in _uri and "://" not in _uri:
            _uri = _uri.replace("postgres:", "postgresql://", 1)
        elif _uri.startswith("postgres://"):
            _uri = _uri.replace("postgres://", "postgresql://", 1)

        # PARCHE CRÍTICO: Si la URI no tiene usuario (formato pass@host)
        # SQLAlchemy confunde el pass con el usuario. Forzamos 'postgres' como usuario.
        # Buscamos si hay un '@' pero no hay un ':' antes de él (excluyendo el esquema)
        scheme_part = _uri.split("://")[0] if "://" in _uri else "postgresql"
        rest = _uri.split("://")[1] if "://" in _uri else _uri
        
        if "@" in rest:
            user_pass_part = rest.split("@")[0]
            if ":" not in user_pass_part:
                # El formato es 'password@host', le agregamos el usuario 'postgres'
                _uri = f"{scheme_part}://postgres:{user_pass_part}@{rest.split('@', 1)[1]}"

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

# Debug seguro
if "SQLALCHEMY_DATABASE_URI" in locals() or "Config" in globals():
    uri_to_print = Config.SQLALCHEMY_DATABASE_URI
    if "@" in uri_to_print:
        print(f"DEBUG: URI de base de datos procesada correctamente")

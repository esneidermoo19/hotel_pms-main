import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

class Config:
    # 1. Obtener la URI y aplicar parches de compatibilidad
    raw_uri = os.getenv("DATABASE_URL", "").strip().replace('\r', '').replace('\n', '')
    
    if raw_uri:
        # Extraer el 'resto' después del esquema (después de : o ://)
        if "://" in raw_uri:
            rest = raw_uri.split("://", 1)[1]
        elif ":" in raw_uri:
            rest = raw_uri.split(":", 1)[1]
        else:
            rest = raw_uri
        
        # Limpiar barras iniciales del resto para evitar /////
        rest = rest.lstrip("/")

        # Si en 'rest' no hay un '@', es probable que falte el usuario 'postgres'
        if "@" in rest:
            user_pass_part = rest.split("@", 1)[0]
            host_part = rest.split("@", 1)[1]
            
            if ":" in user_pass_part:
                # Ya tiene usuario:password
                final_netloc = rest
            else:
                # Solo tiene password, le agregamos el usuario postgres
                final_netloc = f"postgres:{user_pass_part}@{host_part}"
        else:
            # No hay @, algo raro. Intentamos usarlo como host o fallback
            final_netloc = rest

        SQLALCHEMY_DATABASE_URI = f"postgresql://{final_netloc}"
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///hotel.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-2024-change-in-production')
    
    # 4. Configuración de Correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Hotel Boutique La Orquidea <laorquideahotel45@gmail.com>')

# Log de verificación
print(f"DEBUG: URI final lista")

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
    
    # 3. Configuración de Seguridad y Autenticación Staff
    # Hash por defecto para PIN "9040" si no se define STAFF_PIN_HASH en el .env
    STAFF_PIN_HASH = os.environ.get(
        'STAFF_PIN_HASH', 
        'scrypt:32768:8:1$4tow0fpPjInTe0Lb$020a84423e3ef2ada619686b64bd1558085d164903a4bb196c4a350e2f6a0e1c110114b364f2954b2f54c9145a441cd96237a215462fcf026cd7674db6cdc190'
    )
    ADMIN_JHONNY_PASS = os.environ.get('ADMIN_JHONNY_PASS', '6556')
    ADMIN_EDWIN_PASS = os.environ.get('ADMIN_EDWIN_PASS', '2345')
    RECEP_ANA_PASS = os.environ.get('RECEP_ANA_PASS', '1234')

    # 4. Configuración de Correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # Google muestra la App Password con espacios ("abcd efgh ijkl mnop");
    # SMTP la rechaza con 535 si se dejan, así que se normaliza aquí.
    _raw_pwd = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_PASSWORD = ''.join(_raw_pwd.split()) or None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Hotel Boutique La Orquidea <laorquideahotel45@gmail.com>')

# Log de verificación
print(f"DEBUG: URI final lista")

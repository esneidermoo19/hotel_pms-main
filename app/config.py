import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

class Config:
    # 1. Obtener la URI y aplicar parches de compatibilidad
    raw_uri = os.getenv("DATABASE_URL", "").strip().replace('\r', '').replace('\n', '')
    
    if raw_uri:
        # Si no tiene esquema (://), le agregamos uno temporal para poder parsearla
        if "://" not in raw_uri:
            # Si empieza con postgres, lo usamos, si no, asumimos postgresql
            if raw_uri.startswith("postgres"):
                raw_uri = raw_uri.replace("postgres", "postgresql://", 1) if not raw_uri.startswith("postgres:") else raw_uri.replace("postgres:", "postgresql://", 1)
            else:
                raw_uri = "postgresql://" + raw_uri

        # Parsear la URL para limpiar sus partes
        parsed = urlparse(raw_uri)
        
        # Corregir esquema
        scheme = "postgresql"
        
        # Corregir usuario y contraseña
        netloc = parsed.netloc
        if "@" in netloc:
            user_pass, host_port = netloc.split("@", 1)
            if ":" in user_pass:
                user, pw = user_pass.split(":", 1)
            else:
                # Si no hay :, asumimos que lo que hay es el password y el user es postgres
                user = "postgres"
                pw = user_pass
            netloc = f"{user}:{pw}@{host_port}"
        else:
            # Si no hay @, es que solo viene el host o algo raro. 
            # En Coolify esto no debería pasar con DATABASE_URL, pero por si acaso:
            netloc = f"postgres@{netloc}"

        # Reconstruir
        SQLALCHEMY_DATABASE_URI = urlunparse((scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
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
print(f"DEBUG: Configuración de base de datos finalizada ({Config.SQLALCHEMY_DATABASE_URI.split(':')[0]}://...)")

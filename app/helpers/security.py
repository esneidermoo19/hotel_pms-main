import os
import logging
from datetime import datetime, timedelta
from flask import request
from app import db
from app.models.audit import AuditLog

# Configuración del logger a archivo
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'audit.log')

logger = logging.getLogger('security_audit')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Almacenamiento en memoria para Rate Limiting
# Estructura: { key: [timestamp1, timestamp2, ...] }
_failed_attempts = {}

class SecurityManager:
    @staticmethod
    def get_client_ip():
        """Obtiene la IP real del cliente detrás de proxies como Coolify/Cloudflare/Nginx"""
        from flask import has_request_context, request
        if has_request_context():
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            return request.remote_addr or '127.0.0.1'
        return '127.0.0.1'

    @staticmethod
    def check_rate_limit(key, max_attempts=5, window_seconds=900):
        """
        Verifica si la clave (IP o IP+Endpoint) superó el límite de intentos.
        Retorna (is_blocked, remaining_seconds, attempts_count)
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        attempts = _failed_attempts.get(key, [])
        # Filtrar solo intentos dentro de la ventana de tiempo
        valid_attempts = [t for t in attempts if t > cutoff]
        _failed_attempts[key] = valid_attempts

        if len(valid_attempts) >= max_attempts:
            # Calcular tiempo restante del bloqueo
            oldest_attempt = min(valid_attempts)
            seconds_left = int((oldest_attempt + timedelta(seconds=window_seconds) - now).total_seconds())
            return True, max(seconds_left, 1), len(valid_attempts)

        return False, 0, len(valid_attempts)

    @staticmethod
    def record_failed_attempt(key):
        """Registra un intento fallido para la clave especificada"""
        now = datetime.utcnow()
        if key not in _failed_attempts:
            _failed_attempts[key] = []
        _failed_attempts[key].append(now)

    @staticmethod
    def reset_attempts(key):
        """Limpia los intentos fallidos al tener un acceso exitoso"""
        if key in _failed_attempts:
            del _failed_attempts[key]

    @staticmethod
    def log_audit_event(event_type, success, username=None, details=None):
        """Registra el evento de seguridad en archivo audit.log y en la tabla AuditLog"""
        ip = SecurityManager.get_client_ip()
        status_str = "SUCCESS" if success else "FAILED"
        msg = f"EVENT={event_type} | STATUS={status_str} | IP={ip} | USER={username or 'N/A'} | DETAILS={details or 'N/A'}"
        
        # 1. Escribir a archivo de logs
        if success:
            logger.info(msg)
        else:
            logger.warning(msg)

        # 2. Registrar en la base de datos
        try:
            log_entry = AuditLog(
                event_type=event_type,
                ip_address=ip,
                username=username,
                success=success,
                details=details
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error guardando AuditLog en DB: {e}")

    @staticmethod
    def sanitize_input(value, max_length=100):
        """Sanitiza y valida una cadena de entrada"""
        if not value:
            return ""
        s = str(value).strip()
        # Eliminar caracteres nulos o de control invisibles
        s = "".join(ch for ch in s if ord(ch) >= 32 or ch in "\n\r\t")
        return s[:max_length]

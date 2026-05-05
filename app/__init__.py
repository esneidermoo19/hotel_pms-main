import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicialización de extensiones
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # 1. Cargar configuración desde app/config.py
    from app.config import Config
    app.config.from_object(Config)

    # 2. Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # Configuración de Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para continuar.'
    login_manager.login_message_category = 'warning'

    # Endpoint de salud para Coolify
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # 3. Registro de Blueprints (Módulos del Hotel)
    from .routes.recep import recep_bp
    from .routes.pos import pos_bp
    from .routes.admin import admin_bp
    from .routes.reportes import reportes_bp
    from .routes.auth import auth_bp
    from .routes.empleado import empleado_bp
    from .routes.cliente import cliente_bp

    app.register_blueprint(recep_bp, url_prefix='/recepcion')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(auth_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(cliente_bp)
    
    # 4. Exenciones de CSRF necesarias para la operatividad
    # Se usan tanto el nombre del endpoint como la ruta completa para asegurar compatibilidad
    csrf.exempt('empleado.nuevo_cliente')
    csrf.exempt('empleado.cobrar_reserva')
    csrf.exempt('empleado.lista_clientes')
    csrf.exempt('app.routes.empleado.nuevo_cliente')
    csrf.exempt('app.routes.empleado.cobrar_reserva')
    csrf.exempt('app.routes.empleado.lista_clientes')

    # 5. Registro de filtros de plantillas
    from app.filters import register_filters
    register_filters(app)

    @app.after_request
    def add_header(response):
        """Prevenir que el navegador guarde en caché páginas protegidas"""
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return app

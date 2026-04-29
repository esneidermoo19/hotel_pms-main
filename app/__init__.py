from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_class=None):
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///hotel.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Disable CSRF protection globally for testing
    app.config['WTF_CSRF_ENABLED'] = False
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register Blueprints
    from .routes.recep import recep_bp
    from .routes.pos import pos_bp
    from .routes.admin import admin_bp
    from .routes.reportes import reportes_bp
    from .routes.auth import auth_bp
    from .routes.empleado import empleado_bp

    app.register_blueprint(recep_bp, url_prefix='/recepcion')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(auth_bp)
    app.register_blueprint(empleado_bp)
    
    # Exempt empleado routes from CSRF
    csrf.exempt('empleado.nuevo_cliente')
    csrf.exempt('empleado.cobrar_reserva')
    csrf.exempt('empleado.lista_clientes')

    # Register currency filter
    @app.template_filter('currency')
    def currency_filter(value):
        if value is None:
            return "0"
        return "{:,}".format(int(value))

    return app
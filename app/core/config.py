import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-weak-key-change-me-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hotel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True') == 'True'
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'jhonnyguerrero653@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'qrjreczs yxqqrbhb')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configurations
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB limit
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    RAW_FOLDER = os.path.join(UPLOAD_FOLDER, 'raw')
    ENCRYPTED_FOLDER = os.path.join(UPLOAD_FOLDER, 'encrypted')
    DECRYPTED_FOLDER = os.path.join(UPLOAD_FOLDER, 'decrypted')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')
    
    # Supported file extensions & magic numbers
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'zip', 'png', 'jpg', 'jpeg', 'mp4', 'csv', 'pptx'}
    
    # Security Session Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True under production HTTPS
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Rate limiting & Lockout settings
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME_MINUTES = 15

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'securevault_dev.db')

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disabled for automated testing ease if desired, though we test CSRF explicitly
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads_test')
    RAW_FOLDER = os.path.join(UPLOAD_FOLDER, 'raw')
    ENCRYPTED_FOLDER = os.path.join(UPLOAD_FOLDER, 'encrypted')
    DECRYPTED_FOLDER = os.path.join(UPLOAD_FOLDER, 'decrypted')

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)
        if os.environ.get('DATABASE_URL')
        else 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'securevault.db')
    )

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}


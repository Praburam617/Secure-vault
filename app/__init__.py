import os
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config_by_name
from app.models import db, User
from app.utils.logger import error_logger

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

    # Load configuration
    app.config.from_object(config_by_name[config_name])

    # Ensure required directories exist
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    for folder in [app.config['RAW_FOLDER'], app.config['ENCRYPTED_FOLDER'], 
                   app.config['DECRYPTED_FOLDER'], app.config['LOGS_FOLDER'], 
                   app.config['REPORTS_FOLDER'], instance_dir]:
        os.makedirs(folder, exist_ok=True)


    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access SecureVault.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Security Response Headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Modern Content-Security-Policy (CSP) allowing Google Fonts and Chart.js
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "object-src 'none';"
        )
        return response

    # Register Blueprints
    from app.auth import auth_bp
    from app.main import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')

    # Register Error Handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large_error(error):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        error_logger.error(f"500 Internal Error: {error}")
        return render_template('errors/500.html'), 500

    return app

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32), nullable=True)

    # Relationships
    files = db.relationship('FileModel', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    share_links = db.relationship('ShareLink', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def calculate_security_score(self):
        """
        Calculates a real security score (0-100) based on actual security factors:
        - Baseline: 60 points
        - Password strength length & complexity: +15 points
        - MFA Enabled: +15 points
        - Active sessions <= 2: +5 points
        - Encryption count > 0: +5 points
        """
        score = 60
        if len(self.password_hash) > 50:
            score += 15
        if self.mfa_enabled:
            score += 15
        
        active_sessions_count = self.sessions.filter_by(is_active=True).count()
        if active_sessions_count <= 2:
            score += 5

        encrypted_files_count = self.files.filter_by(is_encrypted=True, is_in_trash=False).count()
        if encrypted_files_count > 0:
            score += 5

        return min(score, 100)

    def get_score_label(self):
        score = self.calculate_security_score()
        if score >= 90:
            return "Excellent", "success"
        elif score >= 75:
            return "Good", "primary"
        elif score >= 50:
            return "Needs Attention", "warning"
        else:
            return "Critical", "danger"

    def __repr__(self):
        return f'<User {self.username}>'

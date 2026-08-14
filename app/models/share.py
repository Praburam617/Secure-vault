from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class ShareLink(db.Model):
    __tablename__ = 'share_links'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    share_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    download_count = db.Column(db.Integer, default=0)
    max_downloads = db.Column(db.Integer, nullable=True) # None = unlimited
    expires_at = db.Column(db.DateTime, nullable=True)   # None = never
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password, method='scrypt')
        else:
            self.password_hash = None

    def check_password(self, password):
        if not self.password_hash:
            return True
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc):
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True

    def __repr__(self):
        return f'<ShareLink {self.share_token}>'

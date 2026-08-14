from datetime import datetime, timezone
from . import db

class FileModel(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(128), nullable=False)
    file_extension = db.Column(db.String(16), nullable=False)
    
    # Cryptographic Metadata
    enc_salt = db.Column(db.String(64), nullable=True)   # Hex-encoded salt for key derivation
    enc_nonce = db.Column(db.String(64), nullable=True)  # Hex-encoded GCM nonce/IV
    sha256_hash = db.Column(db.String(64), nullable=False) # Original plaintext SHA-256
    ciphertext_hash = db.Column(db.String(64), nullable=True) # Encrypted file SHA-256

    # Flags & State
    is_encrypted = db.Column(db.Boolean, default=True)
    is_shared = db.Column(db.Boolean, default=False)
    is_in_trash = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    retention_days = db.Column(db.Integer, default=0) # 0 = Never, 1 = 24h, 7 = 7d, 30 = 30d

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    share_links = db.relationship('ShareLink', backref='file', lazy='dynamic', cascade='all, delete-orphan')

    def formatted_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def __repr__(self):
        return f'<FileModel {self.original_filename}>'

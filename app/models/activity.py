from datetime import datetime, timezone
from . import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(64), nullable=False, index=True) # login, upload, encrypt, decrypt, share, delete, etc.
    status = db.Column(db.String(32), nullable=False) # SUCCESS, FAILED, WARNING
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.status}>'

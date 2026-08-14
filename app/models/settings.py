from . import db

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    login_alerts = db.Column(db.Boolean, default=True)
    default_retention_days = db.Column(db.Integer, default=0) # 0 = Never
    theme = db.Column(db.String(16), default='dark') # dark, light, system
    reduced_motion = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<UserSettings for User {self.user_id}>'

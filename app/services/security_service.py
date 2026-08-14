from datetime import datetime, timezone, timedelta
from app.models import db, ActivityLog, User
from app.utils.logger import security_logger, activity_logger

class SecurityService:
    @staticmethod
    def log_event(user_id: int, action: str, status: str, ip_address: str = None, user_agent: str = None, details: str = None):
        """
        Creates an audit entry in the database and writes to rotating log files.
        Never logs passwords, tokens, or plaintext payload keys.
        """
        try:
            log_entry = ActivityLog(
                user_id=user_id,
                action=action,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent[:255] if user_agent else None,
                details=details
            )
            db.session.add(log_entry)
            db.session.commit()

            msg = f"User: {user_id} | Action: {action} | Status: {status} | IP: {ip_address} | Details: {details}"
            if status == 'FAILED' or 'ALERT' in action.upper():
                security_logger.warning(msg)
            else:
                activity_logger.info(msg)
        except Exception as e:
            db.session.rollback()

    @staticmethod
    def record_failed_login(user: User):
        """Increments failed login attempt counter and sets lockout timestamp if threshold exceeded."""
        if not user:
            return
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.session.commit()

    @staticmethod
    def reset_failed_login(user: User):
        """Resets failed login attempt counter upon successful login."""
        if not user:
            return
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

    @staticmethod
    def is_user_locked_out(user: User) -> tuple:
        """Returns (is_locked, time_remaining_minutes)."""
        if not user or not user.lockout_until:
            return False, 0
        now = datetime.now(timezone.utc)
        lockout = user.lockout_until.replace(tzinfo=timezone.utc) if user.lockout_until.tzinfo is None else user.lockout_until
        if now < lockout:
            remaining = int((lockout - now).total_seconds() / 60) + 1
            return True, remaining
        else:
            # Lockout expired
            user.failed_login_attempts = 0
            user.lockout_until = None
            db.session.commit()
            return False, 0

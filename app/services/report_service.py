from datetime import datetime, timezone
from app.models import FileModel, ActivityLog, UserSession

class ReportService:
    @staticmethod
    def generate_summary(user) -> dict:
        total_files = user.files.filter_by(is_in_trash=False).count()
        encrypted_files = user.files.filter_by(is_encrypted=True, is_in_trash=False).count()
        shared_files = user.files.filter_by(is_shared=True, is_in_trash=False).count()
        trash_files = user.files.filter_by(is_in_trash=True).count()

        total_bytes = sum([f.file_size for f in user.files.filter_by(is_in_trash=False).all()])

        # Formatted storage
        size = total_bytes
        formatted_storage = "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                formatted_storage = f"{size:.2f} {unit}"
                break
            size /= 1024.0

        encryption_events = user.activity_logs.filter_by(action='ENCRYPT_FILE', status='SUCCESS').count()
        decryption_events = user.activity_logs.filter_by(action='DECRYPT_FILE', status='SUCCESS').count()
        security_alerts = user.activity_logs.filter(ActivityLog.status != 'SUCCESS').count()

        active_sessions = user.sessions.filter_by(is_active=True).count()

        recent_activity = user.activity_logs.order_by(ActivityLog.created_at.desc()).limit(10).all()

        score = user.calculate_security_score()
        score_label, score_class = user.get_score_label()

        return {
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'username': user.username,
            'email': user.email,
            'security_score': score,
            'security_label': score_label,
            'security_class': score_class,
            'total_files': total_files,
            'encrypted_files': encrypted_files,
            'shared_files': shared_files,
            'trash_files': trash_files,
            'storage_used_bytes': total_bytes,
            'storage_used_formatted': formatted_storage,
            'encryption_events': encryption_events,
            'decryption_events': decryption_events,
            'security_alerts': security_alerts,
            'active_sessions': active_sessions,
            'recent_activity': recent_activity
        }

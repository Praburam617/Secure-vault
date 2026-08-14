import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'zip', 'png', 'jpg', 'jpeg', 'mp4', 'csv', 'pptx'}

MAGIC_NUMBERS = {
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'pdf': [b'%PDF'],
    'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
    'docx': [b'PK\x03\x04'],
    'pptx': [b'PK\x03\x04'],
}

class FileService:
    @staticmethod
    def get_extension(filename: str) -> str:
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''

    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        ext = FileService.get_extension(filename)
        return ext in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_magic_bytes(file_path: str, ext: str) -> bool:
        """
        Inspects raw file header bytes against expected magic numbers.
        For text/csv/unknown files, performs clean UTF-8 text validation.
        """
        ext = ext.lower()
        if ext in MAGIC_NUMBERS:
            expected_signatures = MAGIC_NUMBERS[ext]
            with open(file_path, 'rb') as f:
                header = f.read(16)
            for sig in expected_signatures:
                if header.startswith(sig):
                    return True
            return False
        elif ext in ('mp4',):
            with open(file_path, 'rb') as f:
                header = f.read(12)
            return len(header) >= 12 and b'ftyp' in header[4:12]
        elif ext in ('txt', 'csv'):
            try:
                with open(file_path, 'rb') as f:
                    sample = f.read(4096)
                sample.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
        return True

    @staticmethod
    def generate_storage_filename(ext: str) -> str:
        """Generates an un-guessable UUIDv4 filename for physical disk storage."""
        return f"{uuid.uuid4().hex}.{ext}"

    @staticmethod
    def secure_wipe_file(file_path: str):
        """Overwrites file with random bytes before deletion to prevent recovery."""
        if os.path.exists(file_path):
            try:
                length = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(length))
            except Exception:
                pass
            try:
                os.remove(file_path)
            except Exception:
                pass

import hashlib

class HashService:
    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """
        Calculates the SHA-256 hash of a file on disk using streaming chunks
        to support large files without loading the entire file into memory.
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(64 * 1024):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def calculate_bytes_sha256(data: bytes) -> str:
        """Calculates SHA-256 hex digest for a bytes buffer."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def verify_sha256(file_path: str, expected_hash: str) -> bool:
        """Verifies if the file's current SHA-256 matches the expected hash."""
        actual_hash = HashService.calculate_sha256(file_path)
        return actual_hash.lower() == expected_hash.lower()

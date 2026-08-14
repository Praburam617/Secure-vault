import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16  # 128 bits
NONCE_SIZE = 12 # 96 bits for GCM
KEY_SIZE = 32   # 256 bits for AES-256
PBKDF2_ITERATIONS = 100_000

class KeyManager:
    @staticmethod
    def generate_salt() -> bytes:
        """Generates a 16-byte cryptographically secure random salt."""
        return os.urandom(SALT_SIZE)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generates a 12-byte cryptographically secure random nonce for AES-GCM."""
        return os.urandom(NONCE_SIZE)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derives a 256-bit symmetric encryption key from a user password and salt
        using PBKDF2-HMAC-SHA256 with 100,000 iterations.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode('utf-8'))

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from .key_manager import KeyManager, SALT_SIZE, NONCE_SIZE
from .hash_service import HashService

class DecryptionService:
    @staticmethod
    def decrypt_file(input_path: str, output_path: str, password: str, expected_raw_sha256: str = None) -> bool:
        """
        Decrypts an AES-256-GCM payload file using password.
        Validates GCM authentication tag and optional original SHA-256 digest.

        Raises:
            ValueError: If password is incorrect, payload is corrupted, or integrity check fails.
        """
        if not os.path.exists(input_path):
            raise ValueError("Encrypted file does not exist.")

        with open(input_path, 'rb') as f:
            salt = f.read(SALT_SIZE)
            nonce = f.read(NONCE_SIZE)
            ciphertext = f.read()

        if len(salt) < SALT_SIZE or len(nonce) < NONCE_SIZE or not ciphertext:
            raise ValueError("Invalid or corrupted file payload.")

        # Re-derive key
        key = KeyManager.derive_key(password, salt)
        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag:
            raise ValueError("Unable to decrypt this file. Please verify your protection password.")
        except Exception:
            raise ValueError("Cryptographic operation failed during decryption.")

        # Write decrypted bytes to destination output file
        with open(output_path, 'wb') as f:
            f.write(plaintext)

        # Integrity verification
        if expected_raw_sha256:
            decrypted_hash = HashService.calculate_sha256(output_path)
            if decrypted_hash.lower() != expected_raw_sha256.lower():
                # Secure cleanup before raising error
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise ValueError("File integrity verification failed. The file may have been modified or corrupted.")

        return True

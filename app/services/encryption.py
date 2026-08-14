import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .key_manager import KeyManager
from .hash_service import HashService

class EncryptionService:
    @staticmethod
    def encrypt_file(input_path: str, output_path: str, password: str):
        """
        Encrypts a file at input_path using AES-256-GCM with a key derived from password.
        Payload layout written to output_path:
          [Salt (16 bytes)][Nonce (12 bytes)][Encrypted Payload + Auth Tag]

        Returns tuple: (salt_hex, nonce_hex, raw_sha256, ciphertext_sha256)
        """
        # 1. Compute SHA-256 digest of original raw plaintext file
        raw_sha256 = HashService.calculate_sha256(input_path)

        # 2. Generate random salt & nonce
        salt = KeyManager.generate_salt()
        nonce = KeyManager.generate_nonce()

        # 3. Derive 256-bit AES key
        key = KeyManager.derive_key(password, salt)
        aesgcm = AESGCM(key)

        # 4. Read raw file content
        with open(input_path, 'rb') as f:
            plaintext = f.read()

        # 5. Encrypt plaintext with AES-256-GCM (appends 16-byte authentication tag automatically)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # 6. Write [salt][nonce][ciphertext] payload to output file
        with open(output_path, 'wb') as f:
            f.write(salt)
            f.write(nonce)
            f.write(ciphertext)

        # 7. Compute ciphertext payload SHA-256 digest
        ciphertext_sha256 = HashService.calculate_sha256(output_path)

        return salt.hex(), nonce.hex(), raw_sha256, ciphertext_sha256

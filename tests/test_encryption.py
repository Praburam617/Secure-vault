import os
import pytest
from app.services.encryption import EncryptionService
from app.services.decryption import DecryptionService
from app.services.key_manager import KeyManager

def test_aes_256_gcm_encryption_decryption_roundtrip(tmp_path):
    original_file = tmp_path / "sample.txt"
    encrypted_file = tmp_path / "sample.txt.enc"
    decrypted_file = tmp_path / "sample_dec.txt"

    original_content = b"TOP SECRET: AES-256-GCM Cryptographic Testing Payload 1234567890"
    original_file.write_bytes(original_content)

    password = "MyStrongEncryptionPassword!2026"

    # 1. Encrypt
    salt1, nonce1, raw_sha256, ciphertext_sha256 = EncryptionService.encrypt_file(
        str(original_file), str(encrypted_file), password
    )

    assert os.path.exists(str(encrypted_file))
    assert salt1 is not None
    assert nonce1 is not None

    # 2. Decrypt with correct password
    success = DecryptionService.decrypt_file(
        str(encrypted_file), str(decrypted_file), password, expected_raw_sha256=raw_sha256
    )
    assert success is True
    assert decrypted_file.read_bytes() == original_content

def test_wrong_password_decryption_rejection(tmp_path):
    original_file = tmp_path / "secret.txt"
    encrypted_file = tmp_path / "secret.txt.enc"
    decrypted_file = tmp_path / "output.txt"

    original_file.write_bytes(b"Sensitive user data payload")

    EncryptionService.encrypt_file(str(original_file), str(encrypted_file), "CorrectPassword123!")

    # Attempt decryption with wrong password
    with pytest.raises(ValueError) as exc_info:
        DecryptionService.decrypt_file(str(encrypted_file), str(decrypted_file), "WrongPassword456!")
    
    assert "verify your protection password" in str(exc_info.value).lower()

def test_unique_nonce_and_salt(tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    enc1 = tmp_path / "f1.enc"
    enc2 = tmp_path / "f2.enc"

    f1.write_bytes(b"Identical Content Payload")
    f2.write_bytes(b"Identical Content Payload")

    salt1, nonce1, _, _ = EncryptionService.encrypt_file(str(f1), str(enc1), "SamePassword123!")
    salt2, nonce2, _, _ = EncryptionService.encrypt_file(str(f2), str(enc2), "SamePassword123!")

    # Nonces and salts MUST be unique even for identical content & password
    assert salt1 != salt2
    assert nonce1 != nonce2

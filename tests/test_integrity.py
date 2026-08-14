import os
import pytest
from app.services.encryption import EncryptionService
from app.services.decryption import DecryptionService
from app.services.hash_service import HashService

def test_sha256_checksum_calculation(tmp_path):
    f = tmp_path / "data.txt"
    f.write_bytes(b"Hello SHA-256 Checksum Verification")
    hash_val = HashService.calculate_sha256(str(f))
    assert len(hash_val) == 64
    assert HashService.verify_sha256(str(f), hash_val) is True

def test_tampered_ciphertext_detection(tmp_path):
    original_file = tmp_path / "tamper_test.txt"
    encrypted_file = tmp_path / "tamper_test.enc"
    decrypted_file = tmp_path / "tamper_out.txt"

    original_file.write_bytes(b"Crucial Financial Records 2026")
    password = "TamperCheckPassword!"

    salt, nonce, raw_hash, enc_hash = EncryptionService.encrypt_file(
        str(original_file), str(encrypted_file), password
    )

    # Tamper with the encrypted file payload (flip byte in ciphertext)
    with open(str(encrypted_file), 'r+b') as f:
        f.seek(35) # Jump past salt (16 bytes) and nonce (12 bytes) into ciphertext
        byte = f.read(1)
        f.seek(35)
        f.write(bytes([ord(byte) ^ 0xFF]))

    # Decryption of tampered ciphertext MUST fail
    with pytest.raises(ValueError) as exc_info:
        DecryptionService.decrypt_file(str(encrypted_file), str(decrypted_file), password, expected_raw_sha256=raw_hash)

    # Ensure no partial or corrupted decrypted file remains on disk
    assert not os.path.exists(str(decrypted_file))

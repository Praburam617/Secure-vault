import io
import pytest
from app.services.file_service import FileService

def test_file_extension_validation():
    assert FileService.validate_file_extension("document.pdf") is True
    assert FileService.validate_file_extension("image.png") is True
    assert FileService.validate_file_extension("script.exe") is False
    assert FileService.validate_file_extension("shell.php") is False

def test_magic_byte_validation(tmp_path):
    png_file = tmp_path / "valid.png"
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")
    assert FileService.validate_magic_bytes(str(png_file), "png") is True

    fake_png = tmp_path / "fake.png"
    fake_png.write_bytes(b"<?php echo 'malicious code'; ?>")
    assert FileService.validate_magic_bytes(str(fake_png), "png") is False

def test_path_traversal_sanitization():
    raw_filename = "../../../etc/passwd"
    from werkzeug.utils import secure_filename
    sanitized = secure_filename(raw_filename)
    assert "../" not in sanitized
    assert sanitized == "etc_passwd"

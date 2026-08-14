# SecureVault — Secure File Encryption & Privacy Platform

> *"Protect your files. Keep control of your data."*

**SecureVault** is an enterprise-grade cybersecurity web application built with Python Flask, SQLite/SQLAlchemy, AES-256-GCM authenticated encryption, SHA-256 integrity verification, Scrypt key derivation, and a modern responsive dark-mode interface.

---

## Key Features & Capabilities

* **AES-256-GCM Encryption**: Authenticated file encryption with unique 16-byte random salts and 12-byte nonces generated for every encryption event.
* **SHA-256 Data Integrity Verification**: Cryptographic checksum calculation pre-encryption and post-decryption ensures zero silent corruption or payload tampering.
* **Multi-Tenant User Isolation (IDOR Protection)**: Every file access, download, decryption, delete, rename, or share operation enforces strict server-side ownership verification (`user_id == current_user.id`).
* **Secure File Upload Hygiene**: Magic byte header inspection, extension restriction (PDF, DOCX, TXT, ZIP, PNG, JPG, MP4, CSV, PPTX), filename sanitization, and random UUID physical storage paths.
* **Brute-Force & Rate Limiting Protection**: Werkzeug Scrypt password hashing, failed attempt tracking, and 15-minute progressive account lockout after 5 consecutive failures.
* **Security Center & Real-Time Score**: Interactive security health score (0-100) dynamically calculated based on active sessions, password strength, and encryption usage.
* **Secure File Sharing**: High-entropy cryptographically random share tokens with optional passcodes, download limits, expiration timers, and audit logging.
* **Security Audit Logging**: Rotating file logs (`system.log`, `activity.log`, `security.log`, `errors.log`) and searchable in-app audit log viewer.
* **Active Session Manager**: View connected devices, IP addresses, and sign out of other active sessions with one click.
* **Dynamic Reports**: Downloadable account security and vault storage digest (JSON / HTML).

---

## Cryptographic Architecture

```
User Selects File & Inputs Protection Password
                       │
                       ▼
        Generate 16-Byte Cryptographic Salt (os.urandom)
        Generate 12-Byte AES-GCM Nonce/IV (os.urandom)
                       │
                       ▼
        PBKDF2-HMAC-SHA256 (100,000 Iterations) / Scrypt KDF
             Derives 256-bit Symmetric Key
                       │
                       ▼
        AES-256-GCM Encryption + Auth Tag Generation
                       │
                       ▼
        Compute SHA-256 Plaintext Digest & Ciphertext Digest
                       │
                       ▼
Payload Storage: [Salt (16B)][Nonce (12B)][Ciphertext + Auth Tag]
```

### Decryption & Tamper Verification Workflow

1. Re-derive 256-bit symmetric key using stored salt and user password.
2. AES-256-GCM decrypts payload. If authentication tag fails or wrong password:
   > *"Unable to decrypt this file. Please verify your protection password."*
3. Compute SHA-256 digest of decrypted bytes and compare against original stored hash. If tampered:
   > *"File integrity verification failed. The file may have been modified or corrupted."*

---

## Project Structure

```
SecureVault/
├── app.py                      # Application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python package requirements
├── README.md                   # Complete documentation
├── .env.example                # Environment variables template
├── .gitignore                  # Git hygiene specification
│
├── instance/                   # SQLite database storage (development)
│   └── securevault_dev.db
│
├── app/                        # Application Package
│   ├── auth/                   # Authentication blueprint (Login, Register, Logout)
│   ├── main/                   # Core application blueprint (Vault, Encrypt, Decrypt, Security)
│   ├── models/                 # SQLAlchemy ORM Data Models
│   ├── services/               # Cryptography, Hash, File, & Security Services
│   └── utils/                  # Input Validators, Loggers, Decorators
│
├── templates/                  # Jinja2 Modular HTML Templates
│   ├── base.html
│   ├── landing.html
│   ├── dashboard.html
│   ├── vault.html
│   ├── encrypt.html
│   ├── security.html
│   ├── activity.html
│   ├── reports.html
│   └── errors/
│
├── static/                     # CSS, JS, Assets
│   ├── css/                    # Dark theme CSS tokens & responsive breakpoints
│   └── js/                     # Vanilla JS canvas, progress bar, drag & drop, strength meter
│
├── uploads/                    # Storage directories (Outside web root)
│   ├── raw/
│   ├── encrypted/
│   └── decrypted/
│
├── logs/                       # Rotating File Logs
└── tests/                      # Automated Test Suite (Pytest)
```

---

## Installation & Local Development Setup

### 1. Prerequisites
* Python 3.8 or higher
* pip

### 2. Environment Setup
```bash
# Clone or navigate to the repository
cd SecureVault

# Copy environment template
cp .env.example .env

# Install required dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```

### 4. Launch Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## OWASP Security Controls Summary

| Security Threat | Mitigation Control Implemented |
| :--- | :--- |
| **SQL Injection** | Parameterized SQLAlchemy ORM queries across all endpoints. |
| **Cross-Site Scripting (XSS)** | Jinja2 auto-escaping + Strict Content Security Policy (CSP) headers. |
| **CSRF** | Flask-WTF CSRF tokens on every POST/PUT form submission. |
| **IDOR / Broken Access Control** | Server-side `user_id == current_user.id` checks on all file operations. |
| **Path Traversal** | `secure_filename()` sanitization & random UUID physical storage paths. |
| **Brute Force & Lockout** | Progressive delay & 15-minute account lockout after 5 failed attempts. |
| **Data Tampering** | AES-256-GCM authentication tag + SHA-256 checksum match verification. |
| **Session Fixation** | `session.clear()` invoked upon successful authentication. |

---

## Production Deployment Checklist

1. Set `FLASK_ENV=production` in `.env`.
2. Configure a strong `SECRET_KEY` via `secrets.token_hex(32)`.
3. Set `SESSION_COOKIE_SECURE=True` for HTTPS.
4. Replace SQLite with PostgreSQL database URI: `DATABASE_URL=postgresql://user:pass@localhost:5432/securevault`.
5. Run using a WSGI server like Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
   ```

---

## License

Copyright &copy; 2026 SecureVault. Engineered with security, privacy, and precision.

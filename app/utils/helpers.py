import secrets
import socket
from flask import request, url_for

def generate_random_token(length=32) -> str:
    """Generates a cryptographically secure random hex token."""
    return secrets.token_hex(length)

def get_client_ip() -> str:
    """Extracts client IP address safely considering reverse proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP').strip()
    return request.remote_addr or '127.0.0.1'

def parse_user_agent() -> str:
    """Returns standard user agent string or default."""
    return request.headers.get('User-Agent', 'Unknown Browser')

def get_lan_ip() -> str:
    """Attempts to discover local LAN IP address so links work on mobile/Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def build_share_url(share_token: str) -> str:
    """Builds share URL, replacing 127.0.0.1/localhost with real LAN IP for mobile accessibility."""
    base_url = url_for('main.access_share', token=share_token, _external=True)
    lan_ip = get_lan_ip()
    if lan_ip and lan_ip != "127.0.0.1":
        base_url = base_url.replace("127.0.0.1", lan_ip).replace("localhost", lan_ip)
    return base_url

from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def anonymous_required(f):
    """Decorator to restrict access to logged-out users only (e.g. login/register pages)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

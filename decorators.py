from functools import wraps
from flask import session, redirect, url_for, flash


def role_required(role, message=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', '').lower()
            if user_role != role.lower():
                flash(message or f"Accès réservé aux {role}s.", "error")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(*roles, message=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', '').lower()
            allowed_roles = [role.lower() for role in roles]
            if user_role not in allowed_roles:
                allowed_str = ', '.join(allowed_roles)
                flash(message or f"Accès réservé aux rôles : {allowed_str}.", "error")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

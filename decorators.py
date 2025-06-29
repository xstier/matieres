from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role', '').lower() != 'admin':
            flash("Accès réservé aux administrateurs.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function




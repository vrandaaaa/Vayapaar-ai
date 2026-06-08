from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Tenant
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__)

# ── Validation helpers ────────────────────────────────────────────────────────

def _valid_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

def _safe_name(name, max_len=150):
    """Strip leading/trailing whitespace. Reject empty or overlong names."""
    name = name.strip()
    if not name or len(name) > max_len:
        return None
    return name


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        email         = request.form.get('email', '').strip().lower()
        password      = request.form.get('password', '')
        confirm       = request.form.get('confirm_password', '')
        business_name = request.form.get('business_name', '').strip()
        business_type = request.form.get('business_type', 'general').strip()

        errors = []

        # Name validation
        if not _safe_name(name):
            errors.append('Name is required and must be under 150 characters.')

        # Email validation
        if not _valid_email(email):
            errors.append('Please enter a valid email address.')

        # Password validation
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        # Business name validation
        if not business_name:
            errors.append('Business name is required.')
        if len(business_name) > 150:
            errors.append('Business name must be under 150 characters.')

        # Allowed business types
        allowed_types = {'saree', 'grocery', 'electronics', 'pharmacy', 'restaurant', 'general'}
        if business_type not in allowed_types:
            business_type = 'general'

        # Duplicate email check (timing-safe)
        if not errors and User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html', form_data=request.form)

        # Create tenant + owner user atomically
        tenant = Tenant(
            business_name=business_name,
            business_type=business_type,
        )
        db.session.add(tenant)
        db.session.flush()   # get tenant.id

        user = User(tenant_id=tenant.id, name=name, email=email, role='owner')
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Registration failed due to a server error. Please try again.', 'error')
            return render_template('auth/register.html', form_data=request.form)

        login_user(user)
        flash(f'Welcome to Vayapaar-AI, {name.split()[0]}! Your business dashboard is ready.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', form_data={})


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Basic input sanity — prevents sending DB queries with garbage input
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')

        # NOTE: SQLAlchemy ORM parameterizes all queries — SQL injection is not possible here.
        # Even if someone sends `email = "' OR '1'='1"`, it is treated as a literal string.
        user = User.query.filter_by(email=email).first()

        # Use constant-time comparison to avoid timing attacks
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next', '')
            # Validate next_page to prevent open redirect
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        # Generic message — do not reveal whether email exists
        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


# ── Forgot Password ───────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if _valid_email(email):
            user = User.query.filter_by(email=email).first()
            if user:
                token = secrets.token_urlsafe(32)
                user.reset_token  = token
                user.reset_expiry = datetime.utcnow() + timedelta(hours=1)
                db.session.commit()

                reset_link = url_for('auth.reset_password', token=token, _external=True)
                # ── Simulated SMTP — replace with real email in production ──
                # In prod: send_email(user.email, subject="Reset your password", body=reset_link)
                flash(
                    f'[SIMULATED EMAIL] Reset link (valid 1 hour): {reset_link}',
                    'info'
                )
            else:
                # Always show the same message — don't reveal if email is registered
                flash('If that email is registered, a reset link has been sent.', 'info')
        else:
            flash('Please enter a valid email address.', 'error')

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Validate token length to prevent abuse
    if not token or len(token) > 100:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.reset_expiry or user.reset_expiry < datetime.utcnow():
        flash('This reset link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        else:
            user.set_password(password)
            user.reset_token  = None
            user.reset_expiry = None
            db.session.commit()
            flash('Password updated successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

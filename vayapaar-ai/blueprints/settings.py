import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Tenant, User
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import uuid

settings_bp = Blueprint('settings', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    tid    = current_user.tenant_id
    tenant = Tenant.query.get_or_404(tid)

    if request.method == 'POST':
        action = request.form.get('action', 'profile')

        # ── Update Business Profile ───────────────────────────────────────────
        if action == 'profile':
            business_name = request.form.get('business_name', '').strip()
            business_type = request.form.get('business_type', 'general').strip()
            phone         = request.form.get('phone', '').strip()[:15]
            address       = request.form.get('address', '').strip()
            gstin         = request.form.get('gstin', '').strip()[:20]
            upi_id        = request.form.get('upi_id', '').strip()[:100]

            errors = []
            if not business_name:
                errors.append('Business name is required.')
            if len(business_name) > 150:
                errors.append('Business name is too long.')

            allowed_types = {'saree','grocery','electronics','pharmacy','restaurant','general'}
            if business_type not in allowed_types:
                business_type = 'general'

            if errors:
                for e in errors:
                    flash(e, 'error')
                return render_template('settings/index.html', tenant=tenant)

            tenant.business_name = business_name
            tenant.business_type = business_type
            tenant.phone         = phone or None
            tenant.address       = address or None
            tenant.gstin         = gstin or None
            tenant.upi_id        = upi_id or None

            # ── Logo Upload ───────────────────────────────────────────────────
            logo = request.files.get('logo')
            if logo and logo.filename:
                if not _allowed_file(logo.filename):
                    flash('Logo must be PNG, JPG, GIF, or WEBP.', 'error')
                    return render_template('settings/index.html', tenant=tenant)

                upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_dir, exist_ok=True)

                ext      = logo.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f'logo_{tid}.{ext}')
                filepath = os.path.join(upload_dir, filename)
                logo.save(filepath)
                tenant.logo_url = f'/static/uploads/{filename}'

            db.session.commit()
            flash('Business profile updated successfully.', 'success')
            return redirect(url_for('settings.index'))

        # ── Change Password ───────────────────────────────────────────────────
        elif action == 'password':
            current_pwd = request.form.get('current_password', '')
            new_pwd     = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_new_password', '')

            if not current_user.check_password(current_pwd):
                flash('Current password is incorrect.', 'error')
            elif len(new_pwd) < 8:
                flash('New password must be at least 8 characters.', 'error')
            elif new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'error')
            else:
                current_user.set_password(new_pwd)
                db.session.commit()
                flash('Password changed successfully.', 'success')
            return redirect(url_for('settings.index'))

        # ── Update Owner Name / Email ─────────────────────────────────────────
        elif action == 'account':
            name  = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()

            import re
            if not name:
                flash('Name is required.', 'error')
            elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                flash('Please enter a valid email address.', 'error')
            else:
                # Check email uniqueness (ignore current user)
                existing = User.query.filter(
                    User.email == email,
                    User.id != current_user.id
                ).first()
                if existing:
                    flash('That email is already registered to another account.', 'error')
                else:
                    current_user.name  = name
                    current_user.email = email
                    db.session.commit()
                    flash('Account details updated.', 'success')
            return redirect(url_for('settings.index'))

    return render_template('settings/index.html', tenant=tenant)

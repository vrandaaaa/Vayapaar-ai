from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Customer, KhataEntry, Sale
import re

cust_bp = Blueprint('customers', __name__)


def _validate_phone(phone):
    """Allow empty or 10-15 digit phone numbers, stripping spaces/dashes."""
    if not phone:
        return ''
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    if cleaned and not re.match(r'^\d{7,15}$', cleaned):
        return None   # signals invalid
    return phone.strip()


@cust_bp.route('/')
@login_required
def index():
    tid = current_user.tenant_id
    q   = request.args.get('q', '').strip()

    query = Customer.query.filter_by(tenant_id=tid)
    if q:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{q}%'),
                Customer.phone.ilike(f'%{q}%'),
            )
        )
    customers = query.order_by(Customer.name).all()
    return render_template('customers/index.html', customers=customers, q=q)


@cust_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        phone        = request.form.get('phone', '').strip()
        email        = request.form.get('email', '').strip().lower()
        address      = request.form.get('address', '').strip()
        credit_raw   = request.form.get('credit_limit', '0').strip()

        errors = []

        if not name:
            errors.append('Customer name is required.')
        if len(name) > 150:
            errors.append('Name is too long (max 150 characters).')

        phone_clean = _validate_phone(phone)
        if phone_clean is None:
            errors.append('Phone number appears invalid.')

        try:
            credit_limit = float(credit_raw)
            if credit_limit < 0:
                errors.append('Credit limit cannot be negative.')
        except ValueError:
            errors.append('Credit limit must be a number.')
            credit_limit = 0.0

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('customers/add.html', form_data=request.form)

        c = Customer(
            tenant_id=current_user.tenant_id,
            name=name,
            phone=phone_clean or None,
            email=email or None,
            address=address or None,
            credit_limit=credit_limit,
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Customer "{name}" added successfully.', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/add.html', form_data={})


@cust_bp.route('/<customer_id>')
@login_required
def detail(customer_id):
    tid      = current_user.tenant_id
    # Tenant-scope enforced — returns 404 if customer belongs to another tenant
    customer = Customer.query.filter_by(id=customer_id, tenant_id=tid).first_or_404()

    # BUG FIX #9: Khata entries also scoped by tenant_id (defense in depth)
    entries = KhataEntry.query.filter_by(
        customer_id=customer_id,
        tenant_id=tid,          # ← explicit tenant guard
    ).order_by(KhataEntry.created_at.desc()).limit(50).all()

    sales = Sale.query.filter_by(
        customer_id=customer_id,
        tenant_id=tid,
    ).order_by(Sale.created_at.desc()).limit(20).all()

    return render_template('customers/detail.html',
        customer=customer,
        entries=entries,
        sales=sales,
    )


@cust_bp.route('/<customer_id>/payment', methods=['POST'])
@login_required
def record_payment(customer_id):
    tid      = current_user.tenant_id
    customer = Customer.query.filter_by(id=customer_id, tenant_id=tid).first_or_404()

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Invalid amount.', 'error')
        return redirect(url_for('customers.detail', customer_id=customer_id))

    note = request.form.get('note', 'Payment received').strip()[:255]

    if amount <= 0:
        flash('Amount must be greater than zero.', 'error')
        return redirect(url_for('customers.detail', customer_id=customer_id))

    if amount > customer.outstanding + 0.01:   # small float tolerance
        flash(f'Amount exceeds outstanding balance of ₹{customer.outstanding:.2f}.', 'error')
        return redirect(url_for('customers.detail', customer_id=customer_id))

    customer.outstanding = round(max(0.0, customer.outstanding - amount), 2)
    entry = KhataEntry(
        tenant_id=tid,
        customer_id=customer_id,
        entry_type='credit',
        amount=amount,
        note=note,
    )
    db.session.add(entry)
    db.session.commit()
    flash(f'Payment of ₹{amount:,.2f} recorded successfully.', 'success')
    return redirect(url_for('customers.detail', customer_id=customer_id))

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Product, Sale, SaleItem, Customer, KhataEntry
import uuid
from datetime import datetime

api_bp = Blueprint('api', __name__)
# NOTE: This entire blueprint is exempted from CSRF in app.py (csrf.exempt(api_bp))
# It is protected instead by login_required on every route.


@api_bp.route('/products/search')
@login_required
def product_search():
    q   = request.args.get('q', '').strip()
    tid = current_user.tenant_id

    if not q:
        return jsonify([])

    products = Product.query.filter(
        Product.tenant_id == tid,
        Product.is_active == True,
        db.or_(
            Product.name.ilike(f'%{q}%'),
            Product.barcode.ilike(f'%{q}%'),
            Product.sku.ilike(f'%{q}%'),
        )
    ).limit(10).all()

    return jsonify([p.to_search_dict() for p in products])


@api_bp.route('/sale/create', methods=['POST'])
@login_required
def create_sale():
    data           = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    tid            = current_user.tenant_id
    items_data     = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    customer_id    = data.get('customer_id') or None
    discount       = float(data.get('discount', 0))

    # ── Input validation ──────────────────────────────────────────────────────
    if not items_data:
        return jsonify({'error': 'Cart is empty'}), 400

    if payment_method not in ('cash', 'upi', 'credit'):
        return jsonify({'error': 'Invalid payment method'}), 400

    if discount < 0:
        return jsonify({'error': 'Discount cannot be negative'}), 400

    # ── Validate and lock items ───────────────────────────────────────────────
    validated_items = []
    for item in items_data:
        # BUG FIX: Reject negative or zero quantities
        try:
            qty = float(item.get('qty', 0))
            unit_price = float(item.get('unit_price', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid quantity or price'}), 400

        if qty <= 0:
            return jsonify({'error': 'Quantity must be greater than zero'}), 400
        if unit_price < 0:
            return jsonify({'error': 'Unit price cannot be negative'}), 400

        # Tenant-scoped product fetch — prevents cross-tenant manipulation
        product = Product.query.filter_by(
            id=item.get('product_id'),
            tenant_id=tid,
            is_active=True
        ).first()

        if not product:
            return jsonify({'error': f'Product not found or unavailable'}), 404

        if product.stock_qty < qty:
            return jsonify({
                'error': f'Insufficient stock for "{product.name}". '
                         f'Available: {product.stock_qty} {product.unit}'
            }), 400

        validated_items.append({
            'product':    product,
            'qty':        qty,
            'unit_price': unit_price,
            'line_total': round(qty * unit_price, 2),
        })

    # ── Validate customer belongs to this tenant ──────────────────────────────
    customer = None
    if customer_id:
        customer = Customer.query.filter_by(id=customer_id, tenant_id=tid).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

    # ── Build sale ────────────────────────────────────────────────────────────
    subtotal = round(sum(i['line_total'] for i in validated_items), 2)

    if discount > subtotal:
        return jsonify({'error': 'Discount cannot exceed subtotal'}), 400

    tax_base = subtotal - discount
    tax      = round(tax_base * 0.18, 2)
    total    = round(tax_base + tax, 2)

    # Snapshot COGS at sale time — immune to future product edits/deletes (BUG FIX #3)
    cogs_snapshot = round(
        sum(i['product'].cost_price * i['qty'] for i in validated_items), 2
    )

    invoice_no = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    sale = Sale(
        id=str(uuid.uuid4()),
        tenant_id=tid,
        customer_id=customer_id,
        invoice_no=invoice_no,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
        cogs_snapshot=cogs_snapshot,
        payment_method=payment_method,
        payment_status='credit' if payment_method == 'credit' else 'paid',
    )
    db.session.add(sale)

    for i in validated_items:
        product = i['product']
        si = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name_snapshot=product.name,   # BUG FIX: snapshot name
            qty=i['qty'],
            unit_price=i['unit_price'],
            cost_price=product.cost_price,         # snapshotted
            line_total=i['line_total'],
        )
        db.session.add(si)
        # Deduct stock
        product.stock_qty = round(product.stock_qty - i['qty'], 4)

    # ── Khata update if credit ────────────────────────────────────────────────
    if payment_method == 'credit' and customer:
        customer.outstanding = round(customer.outstanding + total, 2)
        entry = KhataEntry(
            tenant_id=tid,
            customer_id=customer_id,
            entry_type='debit',
            amount=total,
            note=f'Sale {invoice_no}',
        )
        db.session.add(entry)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error. Please try again.'}), 500

    return jsonify({
        'success':    True,
        'invoice_no': invoice_no,
        'sale_id':    sale.id,
        'total':      total,
    })


@api_bp.route('/customers/search')
@login_required
def customer_search():
    q   = request.args.get('q', '').strip()
    tid = current_user.tenant_id

    if not q:
        return jsonify([])

    from models import Customer
    customers = Customer.query.filter(
        Customer.tenant_id == tid,
        db.or_(
            Customer.name.ilike(f'%{q}%'),
            Customer.phone.ilike(f'%{q}%'),
        )
    ).limit(8).all()

    return jsonify([{
        'id':          c.id,
        'name':        c.name,
        'phone':       c.phone or '',
        'outstanding': c.outstanding,
    } for c in customers])

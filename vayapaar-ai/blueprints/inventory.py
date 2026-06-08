from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Product, Category, ProductVariant
from datetime import date

inv_bp = Blueprint('inventory', __name__)

ALLOWED_UNITS = {'pcs', 'kg', 'g', 'l', 'ml', 'm', 'ft', 'box', 'dozen', 'pair'}
ALLOWED_TYPES = {'simple', 'variant', 'serial', 'expiry'}


def _safe_float(value, default=0.0, minimum=None):
    """Parse a float safely; return default on failure; enforce minimum if given."""
    try:
        result = float(str(value).strip())
        if minimum is not None:
            result = max(minimum, result)
        return result
    except (TypeError, ValueError):
        return default


@inv_bp.route('/')
@login_required
def index():
    tid        = current_user.tenant_id
    cats       = Category.query.filter_by(tenant_id=tid).order_by(Category.name).all()
    cat_filter = request.args.get('cat', '').strip()
    q          = request.args.get('q', '').strip()

    query = Product.query.filter_by(tenant_id=tid, is_active=True)
    if cat_filter:
        query = query.filter_by(category_id=cat_filter)
    if q:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{q}%'),
                Product.sku.ilike(f'%{q}%'),
                Product.barcode.ilike(f'%{q}%'),
            )
        )

    products = query.order_by(Product.name).all()
    return render_template('inventory/index.html',
        products=products, categories=cats,
        cat_filter=cat_filter, q=q)


@inv_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    tid  = current_user.tenant_id
    cats = Category.query.filter_by(tenant_id=tid).order_by(Category.name).all()

    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        sku          = request.form.get('sku', '').strip()[:100]
        barcode      = request.form.get('barcode', '').strip()[:100]
        cat_id       = request.form.get('category_id', '').strip() or None
        product_type = request.form.get('product_type', 'simple').strip()
        unit         = request.form.get('unit', 'pcs').strip()

        # ── Boundary validation ───────────────────────────────────────────────
        errors = []

        if not name:
            errors.append('Product name is required.')
        if len(name) > 200:
            errors.append('Product name is too long (max 200 chars).')

        if product_type not in ALLOWED_TYPES:
            errors.append('Invalid product type.')
            product_type = 'simple'

        if unit not in ALLOWED_UNITS:
            errors.append(f'Invalid unit. Choose from: {", ".join(sorted(ALLOWED_UNITS))}.')
            unit = 'pcs'

        cost_price  = _safe_float(request.form.get('cost_price'), 0.0, minimum=0.0)
        sell_price  = _safe_float(request.form.get('selling_price'), 0.0, minimum=0.0)
        stock       = _safe_float(request.form.get('stock_qty'), 0.0, minimum=0.0)  # BUG FIX: no negative stock
        low_stock   = _safe_float(request.form.get('low_stock_threshold'), 5.0, minimum=0.0)

        if sell_price <= 0:
            errors.append('Selling price must be greater than zero.')

        # Validate category belongs to this tenant
        if cat_id:
            valid_cat = Category.query.filter_by(id=cat_id, tenant_id=tid).first()
            if not valid_cat:
                errors.append('Invalid category selected.')
                cat_id = None

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('inventory/add.html', categories=cats, form_data=request.form)

        product = Product(
            tenant_id=tid,
            name=name,
            sku=sku or None,
            barcode=barcode or None,
            category_id=cat_id,
            product_type=product_type,
            cost_price=cost_price,
            selling_price=sell_price,
            stock_qty=stock,
            low_stock_threshold=low_stock,
            unit=unit,
        )
        db.session.add(product)
        db.session.flush()   # get product.id before adding variants

        # ── Variants ──────────────────────────────────────────────────────────
        if product_type in ALLOWED_TYPES - {'simple'}:
            variant_names    = request.form.getlist('variant_name')
            variant_serials  = request.form.getlist('serial_number')
            variant_expiries = request.form.getlist('expiry_date')
            variant_prices   = request.form.getlist('extra_price')
            variant_qtys     = request.form.getlist('variant_qty')

            for i, vname in enumerate(variant_names):
                vname = vname.strip()
                if not vname:
                    continue

                exp = None
                if variant_expiries and i < len(variant_expiries) and variant_expiries[i]:
                    try:
                        exp = date.fromisoformat(variant_expiries[i])
                    except ValueError:
                        pass

                serial = (variant_serials[i].strip() if variant_serials and i < len(variant_serials) else None) or None
                extra  = _safe_float(variant_prices[i] if variant_prices and i < len(variant_prices) else 0, 0.0, minimum=0.0)
                vqty   = _safe_float(variant_qtys[i] if variant_qtys and i < len(variant_qtys) else 0, 0.0, minimum=0.0)

                db.session.add(ProductVariant(
                    product_id=product.id,
                    variant_name=vname,
                    serial_number=serial,
                    expiry_date=exp,
                    extra_price=extra,
                    qty=vqty,
                ))

        db.session.commit()
        flash(f'Product "{name}" added successfully.', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/add.html', categories=cats, form_data={})


@inv_bp.route('/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    tid     = current_user.tenant_id
    product = Product.query.filter_by(id=product_id, tenant_id=tid).first_or_404()
    cats    = Category.query.filter_by(tenant_id=tid).order_by(Category.name).all()

    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        unit  = request.form.get('unit', 'pcs').strip()
        errors = []

        if not name:
            errors.append('Product name is required.')
        if unit not in ALLOWED_UNITS:
            errors.append('Invalid unit.')
            unit = product.unit

        sell_price = _safe_float(request.form.get('selling_price'), product.selling_price, minimum=0.01)
        if sell_price <= 0:
            errors.append('Selling price must be greater than zero.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('inventory/edit.html', product=product, categories=cats)

        cat_id = request.form.get('category_id', '').strip() or None
        if cat_id:
            valid_cat = Category.query.filter_by(id=cat_id, tenant_id=tid).first()
            if not valid_cat:
                cat_id = product.category_id

        product.name          = name
        product.sku           = request.form.get('sku', '').strip()[:100] or None
        product.barcode       = request.form.get('barcode', '').strip()[:100] or None
        product.category_id   = cat_id
        product.unit          = unit
        product.cost_price    = _safe_float(request.form.get('cost_price'), product.cost_price, minimum=0.0)
        product.selling_price = sell_price
        product.stock_qty     = _safe_float(request.form.get('stock_qty'), product.stock_qty, minimum=0.0)
        product.low_stock_threshold = _safe_float(
            request.form.get('low_stock_threshold'), product.low_stock_threshold, minimum=0.0
        )

        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/edit.html', product=product, categories=cats)


@inv_bp.route('/delete/<product_id>', methods=['POST'])
@login_required
def delete(product_id):
    tid     = current_user.tenant_id
    product = Product.query.filter_by(id=product_id, tenant_id=tid).first_or_404()
    product.is_active = False   # soft delete — preserves sale history
    db.session.commit()
    flash(f'"{product.name}" has been archived.', 'success')
    return redirect(url_for('inventory.index'))


@inv_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name', '').strip()[:100]
    if not name:
        flash('Category name cannot be empty.', 'error')
        return redirect(url_for('inventory.index'))

    tid = current_user.tenant_id
    # Prevent duplicate category names per tenant
    existing = Category.query.filter_by(tenant_id=tid, name=name).first()
    if existing:
        flash(f'Category "{name}" already exists.', 'error')
        return redirect(url_for('inventory.index'))

    cat = Category(tenant_id=tid, name=name)
    db.session.add(cat)
    db.session.commit()
    flash(f'Category "{name}" added.', 'success')
    return redirect(url_for('inventory.index'))

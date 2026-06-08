from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Product, Sale, SaleItem, Category
from sqlalchemy import func
from datetime import datetime, timedelta, date

dash_bp = Blueprint('dashboard', __name__)


@dash_bp.route('/')
@login_required
def index():
    tid         = current_user.tenant_id
    today       = date.today()
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())
    today_start = datetime.combine(today, datetime.min.time())

    # ── KPIs ──────────────────────────────────────────────────────────────────
    today_sales = db.session.query(func.sum(Sale.total)).filter(
        Sale.tenant_id == tid,
        Sale.created_at >= today_start,
    ).scalar() or 0.0

    month_revenue = db.session.query(func.sum(Sale.total)).filter(
        Sale.tenant_id == tid,
        Sale.created_at >= month_start,
    ).scalar() or 0.0

    # BUG FIX #3: Use cogs_snapshot on Sale model — no JOIN to Product needed.
    # This means profit is correct even if products are later edited or deleted.
    month_cogs = db.session.query(func.sum(Sale.cogs_snapshot)).filter(
        Sale.tenant_id == tid,
        Sale.created_at >= month_start,
    ).scalar() or 0.0

    gross_profit = month_revenue - month_cogs
    net_profit   = round(gross_profit * 0.85, 2)   # 15% operating expenses

    # ── Low stock items ───────────────────────────────────────────────────────
    low_stock_items = Product.query.filter(
        Product.tenant_id == tid,
        Product.is_active == True,
        Product.stock_qty <= Product.low_stock_threshold,
    ).order_by(Product.stock_qty.asc()).limit(12).all()

    # ── Top categories by revenue this month ──────────────────────────────────
    # BUG FIX #5: Convert Row objects to plain dicts for tojson serialization
    top_cats_raw = db.session.query(
        Category.name,
        func.sum(SaleItem.line_total).label('revenue'),
    ).join(Product,  Product.category_id == Category.id)\
     .join(SaleItem, SaleItem.product_id  == Product.id)\
     .join(Sale,     Sale.id              == SaleItem.sale_id)\
     .filter(
         Sale.tenant_id  == tid,
         Category.tenant_id == tid,
         Sale.created_at >= month_start,
     )\
     .group_by(Category.name)\
     .order_by(func.sum(SaleItem.line_total).desc())\
     .limit(6).all()

    # Safe for tojson — plain Python list of dicts
    top_cats = [{'name': row.name, 'revenue': float(row.revenue)} for row in top_cats_raw]

    # ── Daily sales last 7 days ───────────────────────────────────────────────
    daily_sales = []
    for i in range(6, -1, -1):
        d     = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end   = datetime.combine(d, datetime.max.time())
        amt = db.session.query(func.sum(Sale.total)).filter(
            Sale.tenant_id  == tid,
            Sale.created_at >= d_start,
            Sale.created_at <= d_end,
        ).scalar() or 0.0
        daily_sales.append({'date': d.strftime('%d %b'), 'amount': round(float(amt), 2)})

    return render_template('dashboard/index.html',
        today_sales=round(float(today_sales), 2),
        month_revenue=round(float(month_revenue), 2),
        gross_profit=round(float(gross_profit), 2),
        net_profit=float(net_profit),
        low_stock_items=low_stock_items,
        top_cats=top_cats,
        daily_sales=daily_sales,
    )

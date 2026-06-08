from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Sale, SaleItem
from sqlalchemy import func
from datetime import datetime, timedelta, date

fin_bp = Blueprint('finance', __name__)


@fin_bp.route('/')
@login_required
def index():
    tid    = current_user.tenant_id
    period = request.args.get('period', 'month')

    today = date.today()
    if period == 'today':
        start = datetime.combine(today, datetime.min.time())
    elif period == 'week':
        start = datetime.combine(today - timedelta(days=7), datetime.min.time())
    elif period == 'year':
        start = datetime.combine(today.replace(month=1, day=1), datetime.min.time())
    else:
        start = datetime.combine(today.replace(day=1), datetime.min.time())

    # ── Aggregate financials ──────────────────────────────────────────────────
    row = db.session.query(
        func.coalesce(func.sum(Sale.total),         0.0).label('revenue'),
        func.coalesce(func.sum(Sale.discount),      0.0).label('total_discount'),
        func.coalesce(func.sum(Sale.tax),           0.0).label('total_tax'),
        func.coalesce(func.sum(Sale.cogs_snapshot), 0.0).label('cogs'),   # BUG FIX #3
        func.count(Sale.id).label('num_sales'),
    ).filter(
        Sale.tenant_id  == tid,
        Sale.created_at >= start,
    ).first()

    revenue        = float(row.revenue)
    total_discount = float(row.total_discount)
    total_tax      = float(row.total_tax)
    cogs           = float(row.cogs)
    num_sales      = int(row.num_sales)

    gross_profit       = round(revenue - cogs, 2)
    operating_expense  = round(gross_profit * 0.15, 2)
    net_profit         = round(gross_profit - operating_expense, 2)

    # ── Daily breakdown for chart (last 30 days) ──────────────────────────────
    daily = []
    for i in range(29, -1, -1):
        d       = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end   = datetime.combine(d, datetime.max.time())

        d_row = db.session.query(
            func.coalesce(func.sum(Sale.total),         0.0).label('total'),
            func.coalesce(func.sum(Sale.cogs_snapshot), 0.0).label('cogs'),
        ).filter(
            Sale.tenant_id  == tid,
            Sale.created_at >= d_start,
            Sale.created_at <= d_end,
        ).first()

        rev  = float(d_row.total)
        cost = float(d_row.cogs)
        daily.append({
            'date':    d.strftime('%d %b'),
            'revenue': round(rev, 2),
            'profit':  round(rev - cost, 2),
        })

    # ── Payment method breakdown ──────────────────────────────────────────────
    # BUG FIX #6: Convert to plain dicts — SQLAlchemy Row is not JSON-serializable
    payment_rows = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.coalesce(func.sum(Sale.total), 0.0).label('total'),
    ).filter(
        Sale.tenant_id  == tid,
        Sale.created_at >= start,
    ).group_by(Sale.payment_method).all()

    payment_summary = [
        {
            'method': r.payment_method,
            'count':  int(r.count),
            'total':  round(float(r.total), 2),
        }
        for r in payment_rows
    ]

    # ── Recent sales ──────────────────────────────────────────────────────────
    recent_sales = Sale.query.filter(
        Sale.tenant_id  == tid,
        Sale.created_at >= start,
    ).order_by(Sale.created_at.desc()).limit(25).all()

    return render_template('finance/index.html',
        period=period,
        revenue=revenue,
        cogs=cogs,
        gross_profit=gross_profit,
        net_profit=net_profit,
        total_discount=total_discount,
        total_tax=total_tax,
        num_sales=num_sales,
        daily=daily,
        payment_summary=payment_summary,
        recent_sales=recent_sales,
        operating_expense=operating_expense,
    )

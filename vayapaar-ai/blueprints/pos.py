from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Sale, Tenant
import qrcode
import io
import base64

pos_bp = Blueprint('pos', __name__)


@pos_bp.route('/')
@login_required
def index():
    return render_template('pos/index.html')


@pos_bp.route('/invoice/<sale_id>')
@login_required
def invoice(sale_id):
    tid    = current_user.tenant_id
    # Tenant-scoped — another tenant cannot print someone else's invoice
    sale   = Sale.query.filter_by(id=sale_id, tenant_id=tid).first_or_404()
    tenant = Tenant.query.get(tid)

    qr_code = None
    if tenant and tenant.upi_id:
        try:
            upi_str = (
                f"upi://pay?pa={tenant.upi_id}"
                f"&pn={tenant.business_name.replace(' ', '%20')}"
                f"&am={sale.total:.2f}&cu=INR&tn=Invoice%20{sale.invoice_no}"
            )
            img = qrcode.make(upi_str)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            qr_code = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            qr_code = None  # QR generation failure is non-fatal

    customer = sale.customer
    return render_template('invoice/print.html',
        sale=sale,
        tenant=tenant,
        customer=customer,
        qr_code=qr_code,
    )

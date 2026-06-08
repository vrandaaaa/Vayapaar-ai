from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


# ─── TENANT ───────────────────────────────────────────────────────────────────
class Tenant(db.Model):
    __tablename__ = 'tenants'
    id            = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    business_name = db.Column(db.String(150), nullable=False)
    business_type = db.Column(db.String(50),  nullable=False, default='general')
    logo_url      = db.Column(db.String(255))
    upi_id        = db.Column(db.String(100))
    address       = db.Column(db.Text)
    gstin         = db.Column(db.String(20))
    phone         = db.Column(db.String(15))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    users      = db.relationship('User',      backref='tenant',   lazy=True, cascade='all,delete-orphan')
    products   = db.relationship('Product',   backref='tenant',   lazy=True, cascade='all,delete-orphan')
    customers  = db.relationship('Customer',  backref='tenant',   lazy=True, cascade='all,delete-orphan')
    sales      = db.relationship('Sale',      backref='tenant',   lazy=True, cascade='all,delete-orphan')
    categories = db.relationship('Category',  backref='tenant',   lazy=True, cascade='all,delete-orphan')


# ─── USER ──────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    tenant_id     = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20),  default='owner')
    reset_token   = db.Column(db.String(100))
    reset_expiry  = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


# ─── CATEGORY ─────────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'categories'
    id        = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name      = db.Column(db.String(100), nullable=False)

    products  = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


# ─── PRODUCT ──────────────────────────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'
    id             = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    tenant_id      = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id    = db.Column(db.Integer,    db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    name           = db.Column(db.String(200), nullable=False)
    sku            = db.Column(db.String(100))
    barcode        = db.Column(db.String(100), index=True)
    product_type   = db.Column(db.String(20),  default='simple')  # simple/variant/serial/expiry
    cost_price     = db.Column(db.Float,  default=0.0,  nullable=False)
    selling_price  = db.Column(db.Float,  nullable=False)
    stock_qty      = db.Column(db.Float,  default=0.0,  nullable=False)
    low_stock_threshold = db.Column(db.Float, default=5.0, nullable=False)
    unit           = db.Column(db.String(20),  default='pcs')
    image_url      = db.Column(db.String(255))
    is_active      = db.Column(db.Boolean, default=True, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    variants   = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all,delete-orphan')
    # NOTE: sale_items intentionally uses passive_deletes — we keep history even if product is archived
    sale_items = db.relationship('SaleItem', backref='product', lazy=True, passive_deletes=True)

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.low_stock_threshold

    def to_search_dict(self):
        return {
            'id':      self.id,
            'name':    self.name,
            'sku':     self.sku or '',
            'barcode': self.barcode or '',
            'price':   self.selling_price,
            'cost':    self.cost_price,
            'stock':   self.stock_qty,
            'unit':    self.unit,
        }


class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    id            = db.Column(db.Integer, primary_key=True)
    product_id    = db.Column(db.String(36), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_name  = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    expiry_date   = db.Column(db.Date)
    extra_price   = db.Column(db.Float, default=0.0)
    qty           = db.Column(db.Float, default=0.0)


# ─── CUSTOMER ─────────────────────────────────────────────────────────────────
class Customer(db.Model):
    __tablename__ = 'customers'
    id           = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    tenant_id    = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    name         = db.Column(db.String(150), nullable=False)
    phone        = db.Column(db.String(15))
    email        = db.Column(db.String(120))
    address      = db.Column(db.Text)
    credit_limit = db.Column(db.Float, default=0.0, nullable=False)
    outstanding  = db.Column(db.Float, default=0.0, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    sales         = db.relationship('Sale',        backref='customer', lazy=True)
    khata_entries = db.relationship('KhataEntry',  backref='customer', lazy=True, cascade='all,delete-orphan')


# ─── KHATA ENTRY ──────────────────────────────────────────────────────────────
class KhataEntry(db.Model):
    __tablename__ = 'khata_entries'
    id          = db.Column(db.Integer, primary_key=True)
    tenant_id   = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    entry_type  = db.Column(db.String(10), nullable=False)   # debit / credit
    amount      = db.Column(db.Float, nullable=False)
    note        = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─── SALE ─────────────────────────────────────────────────────────────────────
class Sale(db.Model):
    __tablename__ = 'sales'
    id             = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    tenant_id      = db.Column(db.String(36), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id    = db.Column(db.String(36), db.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    invoice_no     = db.Column(db.String(50), unique=True, nullable=False)
    subtotal       = db.Column(db.Float, default=0.0, nullable=False)
    discount       = db.Column(db.Float, default=0.0, nullable=False)
    tax            = db.Column(db.Float, default=0.0, nullable=False)
    total          = db.Column(db.Float, default=0.0, nullable=False)
    # Snapshot COGS at the time of sale — immune to product edits/deletes
    cogs_snapshot  = db.Column(db.Float, default=0.0, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')
    payment_status = db.Column(db.String(20), default='paid')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all,delete-orphan')


class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id          = db.Column(db.Integer, primary_key=True)
    sale_id     = db.Column(db.String(36), db.ForeignKey('sales.id',    ondelete='CASCADE'), nullable=False)
    # SET NULL so finance history survives product archival — cost is snapshotted below
    product_id  = db.Column(db.String(36), db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    product_name_snapshot = db.Column(db.String(200), nullable=False)   # ← FIX: snapshot name
    variant_id  = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True)
    qty         = db.Column(db.Float, nullable=False)
    unit_price  = db.Column(db.Float, nullable=False)
    cost_price  = db.Column(db.Float, default=0.0, nullable=False)   # snapshotted at sale time
    line_total  = db.Column(db.Float, nullable=False)

    @property
    def display_name(self):
        """Always show name even if product was archived."""
        if self.product:
            return self.product.name
        return self.product_name_snapshot or 'Deleted Product'

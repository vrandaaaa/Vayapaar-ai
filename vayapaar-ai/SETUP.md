# Vayapaar-AI Global — Complete Setup Guide

**5,058 lines · 36 files · Zero external dependencies beyond pip**

---

## Complete File Tree

```
vayapaar-ai/
│
├── 📄 app.py                        Application factory + blueprint wiring
├── 📄 models.py                     All SQLAlchemy ORM models
├── 📄 config.py                     Dev / Prod / Test configuration classes
├── 📄 translations.py               EN / Hindi / Hinglish dictionary (300 keys)
├── 📄 requirements.txt              Pinned pip dependencies
├── 📄 .env                          Environment variables (copy & edit)
│
├── 📁 blueprints/
│   ├── __init__.py                  Python package marker
│   ├── api.py                       JSON REST API (CSRF-exempt, login-protected)
│   ├── auth.py                      Register / Login / Forgot & Reset Password
│   ├── customers.py                 Customer CRUD + Khata ledger
│   ├── dashboard.py                 KPI aggregations + chart data
│   ├── finance.py                   P&L, COGS snapshot, payment breakdown
│   ├── inventory.py                 Product CRUD + variant management
│   ├── pos.py                       POS terminal + thermal invoice route
│   └── settings.py                  Business profile + account + password
│
├── 📁 templates/
│   ├── base.html                    Glassmorphism sidebar, dark mode, CSRF JS
│   ├── auth/
│   │   ├── login.html               Eye-toggle, remember-me
│   │   ├── register.html            Business type cards, password strength meter
│   │   ├── forgot_password.html     Simulated SMTP reset flow
│   │   └── reset_password.html      Token-validated password reset
│   ├── dashboard/
│   │   └── index.html               4 KPI cards, 7-day chart, doughnut, low-stock
│   ├── inventory/
│   │   ├── index.html               Filterable table, hover actions, margin badge
│   │   ├── add.html                 Live margin calc, dynamic variant rows
│   │   └── edit.html                Inline margin feedback
│   ├── pos/
│   │   └── index.html               Full POS terminal, customer autocomplete
│   ├── finance/
│   │   └── index.html               Period filter, P&L cards, bar+line chart
│   ├── customers/
│   │   ├── index.html               Card grid, credit progress bars
│   │   ├── add.html                 Credit limit setup
│   │   └── detail.html              Khata ledger, quick-pay buttons, sales history
│   ├── settings/
│   │   └── index.html               Logo upload, profile, account, password change
│   ├── invoice/
│   │   └── print.html               80mm thermal layout with UPI QR code
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
└── 📁 static/
    └── uploads/                     Business logos (auto-created on first upload)
        └── .gitkeep
```

---

## One-Shot Setup (copy-paste the whole block)

```bash
# 1. Clone / unzip project, then enter directory
cd vayapaar-ai

# 2. Create virtual environment
python -m venv venv

# 3. Activate
# macOS / Linux:
source venv/bin/activate
# Windows CMD:
venv\Scripts\activate.bat
# Windows PowerShell:
venv\Scripts\Activate.ps1

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Generate a secure secret key and write to .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# 6. Create uploads directory
mkdir -p static/uploads

# 7. Run
python app.py
```

Open **http://127.0.0.1:5000** → Register your business → Done.

---

## Smoke Test Checklist (run after first launch)

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Open http://127.0.0.1:5000 | Redirects to `/auth/login` |
| 2 | Click "Create your business account" | Register form loads with business type cards |
| 3 | Fill register form & submit | Redirects to `/dashboard/` with welcome message |
| 4 | Click **Inventory → Add Product** | Add form loads; select "Variant" type to see dynamic rows |
| 5 | Save a product with cost ₹100, price ₹150 | Margin shows 33.3% in green |
| 6 | Go to **POS** → search product name | Product appears in dropdown |
| 7 | Add to cart, set discount, click Complete Sale | Invoice modal appears with total |
| 8 | Click "Print Bill" | 80mm invoice opens in new tab |
| 9 | Go to **Finance** | Revenue and profit cards show the sale |
| 10 | Add a customer with Credit Limit ₹5000 | Customer card shows progress bar |
| 11 | Make a Credit sale to that customer | Outstanding balance appears in Khata |
| 12 | Click **Settings** | Business profile form loads |
| 13 | Click language toggle **हि** | All nav labels switch to Hindi |
| 14 | Click language toggle **HG** | Hinglish labels appear |
| 15 | Click moon icon | Dark mode persists on page reload |
| 16 | Logout → try to access /dashboard | Redirected to login |

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(unsafe dev default)* | **MUST change in production** |
| `DATABASE_URL` | `sqlite:///vayapaar.db` | PostgreSQL URI for production |
| `FLASK_ENV` | `development` | Set to `production` for live |

---

## Switching to PostgreSQL

```bash
# 1. Install PostgreSQL and create database
createdb vayapaar

# 2. Update .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/vayapaar

# 3. Install psycopg2 (already in requirements.txt)
# 4. Run app — tables are created automatically via db.create_all()
python app.py
```

---

## Production Deployment (Gunicorn + Nginx)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000 --timeout 120

# Minimal Nginx config
# server {
#     listen 80;
#     server_name yourdomain.com;
#     location / { proxy_pass http://127.0.0.1:8000; }
#     location /static { alias /path/to/vayapaar-ai/static; }
# }
```

---

## Security Hardening Before Going Live

- [ ] Set `SECRET_KEY` to a random 64-character hex string
- [ ] Set `FLASK_ENV=production` (disables debug tracebacks)
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS (Let's Encrypt via Certbot)
- [ ] Replace simulated SMTP in `blueprints/auth.py` with real email (Flask-Mail / SendGrid)
- [ ] Add rate limiting to login: `pip install Flask-Limiter`
- [ ] Set `SESSION_COOKIE_SECURE=True` in `config.py` ProductionConfig
- [ ] Move `static/uploads/` to cloud storage (AWS S3 / Cloudflare R2)
- [ ] Run `pip audit` to check for CVEs in dependencies

---

## Architecture Summary

```
Browser
  │
  ├─ GET /dashboard  →  blueprints/dashboard.py  →  templates/dashboard/index.html
  ├─ GET /pos        →  blueprints/pos.py         →  templates/pos/index.html
  ├─ POST /api/sale/create  →  blueprints/api.py  →  JSON response
  │                              │
  │                              ├─ Validates tenant isolation (tenant_id scoping)
  │                              ├─ Snapshots cost_price + product_name at sale time
  │                              ├─ Deducts stock atomically
  │                              └─ Updates Khata if payment_method == 'credit'
  │
  └─ Multi-Tenancy: every DB query filtered by current_user.tenant_id
```

**Data Isolation Guarantee:** Every single database query across all 8 blueprints is
filtered by `tenant_id`. Vendor A physically cannot read, modify, or delete
Vendor B's data — even with a valid session cookie.

---

*Vayapaar-AI Global · Built with Flask + SQLAlchemy + Tailwind CSS · 5,058 lines*

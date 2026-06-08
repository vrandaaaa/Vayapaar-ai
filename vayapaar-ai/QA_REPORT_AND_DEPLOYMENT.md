# Vayapaar-AI Global — QA Report & Deployment Guide
## Senior QA + DevOps Engineer Sign-off

---

## COMPLETE FILE TREE STRUCTURE

```
vayapaar-ai/
│
├── .env                          ← Environment variables (never commit to git)
├── app.py                        ← Application factory + blueprint registration
├── config.py                     ← Dev/Prod config classes
├── models.py                     ← All SQLAlchemy models
├── translations.py               ← EN / Hindi / Hinglish dictionary
├── requirements.txt              ← Pinned dependencies
│
├── blueprints/
│   ├── __init__.py               ← Package marker (empty, required)
│   ├── api.py                    ← JSON API endpoints (CSRF-exempt, login-protected)
│   ├── auth.py                   ← Register / Login / Forgot-Password / Reset
│   ├── customers.py              ← Customer CRUD + Khata ledger
│   ├── dashboard.py              ← KPI aggregations + chart data
│   ├── finance.py                ← P&L, COGS, payment breakdown
│   ├── inventory.py              ← Product CRUD + category management
│   └── pos.py                    ← POS page + invoice print route
│
├── templates/
│   ├── base.html                 ← Sidebar layout, dark mode, CSRF JS helper
│   ├── errors/
│   │   ├── 404.html
│   │   └── 500.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── forgot_password.html
│   │   └── reset_password.html
│   ├── dashboard/
│   │   └── index.html
│   ├── inventory/
│   │   ├── index.html
│   │   ├── add.html
│   │   └── edit.html
│   ├── pos/
│   │   └── index.html
│   ├── finance/
│   │   └── index.html
│   ├── customers/
│   │   ├── index.html
│   │   ├── add.html
│   │   └── detail.html
│   └── invoice/
│       └── print.html
│
└── static/                       ← (create manually; used for logo uploads)
    └── uploads/
```

---

## BUGS FOUND & FIXED — SUMMARY TABLE

| # | Bug | Severity | File | Fix Applied |
|---|-----|----------|------|-------------|
| 1 | Blueprint imports inside create_app() would cause ModuleNotFoundError on startup | **CRITICAL** | app.py | Fixed imports + blueprints/__init__.py |
| 2 | `now` variable missing from context processor; dashboard crashed with NameError | **CRITICAL** | app.py | Added `now=datetime.utcnow()` to context_processor |
| 3 | Finance COGS query joined Product table — profit became ₹0 for archived products | **HIGH** | models.py, api.py, dashboard.py, finance.py | Added `cogs_snapshot` column to Sale; all profit queries now use snapshot |
| 4 | POS `fetch()` calls had no CSRF token — all sales returned HTTP 400 | **CRITICAL** | app.py, base.html, pos/index.html | CSRF-exempted api blueprint; added `apiFetch()` JS helper with X-CSRFToken |
| 5 | SQLAlchemy Row objects passed to `tojson` in dashboard — TypeError crash | **HIGH** | blueprints/dashboard.py | Converted to `[{'name': r.name, 'revenue': float(r.revenue)}]` plain dicts |
| 6 | Same serialization crash in finance payment_summary | **HIGH** | blueprints/finance.py | Converted to list of plain dicts |
| 7 | Negative qty in cart API body could increase stock while creating a fake sale | **SECURITY** | blueprints/api.py | Added `qty <= 0` and `unit_price < 0` guards |
| 8 | Sidebar active-state used string `in` on endpoint — fragile; 'pos' matches 'deposit' | **LOW** | templates/base.html | Changed to `request.blueprint == 'blueprint_name'` |
| 9 | KhataEntry query lacked tenant_id filter — defense-in-depth gap | **MEDIUM** | blueprints/customers.py | Added `tenant_id=tid` to KhataEntry query |
| 10 | Negative stock_qty accepted via inventory form | **MEDIUM** | blueprints/inventory.py | Added `minimum=0.0` to `_safe_float()` helper for all stock fields |
| 11 | Product name not snapshotted in SaleItem — archived product showed null name in invoices | **MEDIUM** | models.py, api.py | Added `product_name_snapshot` column + `display_name` property |
| 12 | Open redirect vulnerability in login `next` parameter | **SECURITY** | blueprints/auth.py | Validate `next` starts with `/` and not `//` |
| 13 | `discount > subtotal` not checked in API — total could go negative | **MEDIUM** | blueprints/api.py | Added `if discount > subtotal` guard |
| 14 | Duplicate category creation per tenant not prevented | **LOW** | blueprints/inventory.py | Added duplicate name check before insert |
| 15 | `qrcode` package needed as `qrcode[pil]` — plain `qrcode` crashes without Pillow | **HIGH** | requirements.txt | Fixed to `qrcode[pil]==7.4.2` |

---

## FINAL LAUNCH CHECKLIST

Run these steps in order. Each step must succeed before proceeding.

### Step 1 — Create project directory
```bash
mkdir vayapaar-ai && cd vayapaar-ai
```

### Step 2 — Create and activate virtual environment
```bash
python -m venv venv

# macOS / Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```
✅ Verify: your prompt should now show `(venv)`

### Step 3 — Copy all files into place
Replicate the file tree above exactly. Ensure:
- `blueprints/__init__.py` exists (even if empty)
- `templates/errors/`, `templates/auth/`, etc. directories all exist
- `static/uploads/` directory exists (create manually):
```bash
mkdir -p static/uploads
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```
✅ Verify no red errors. If `psycopg2-binary` fails on Windows, it can be removed from requirements.txt (only needed for PostgreSQL).

### Step 5 — Set up environment file
Copy `.env` to project root and set your own `SECRET_KEY`:
```bash
# Generate a strong secret key:
python -c "import secrets; print(secrets.token_hex(32))"
# Paste the result into .env as SECRET_KEY=...
```

### Step 6 — Verify Python can import everything
```bash
python -c "from app import app; print('✅ App imports OK')"
```
If you see `ModuleNotFoundError`: check that `blueprints/__init__.py` exists and all blueprint files are in place.

### Step 7 — Run the application
```bash
python app.py
```
Expected output:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Step 8 — First-time smoke test
Open http://127.0.0.1:5000 in browser.
1. ✅ Redirects to `/auth/login`
2. ✅ Click "Create your business" → register form loads
3. ✅ Register → redirected to `/dashboard/`
4. ✅ Sidebar shows your business name
5. ✅ Click Inventory → Add Product → save a product
6. ✅ Click POS → search product → add to cart → Complete Sale
7. ✅ Invoice modal appears → Print Bill opens thermal invoice
8. ✅ Finance page shows the sale revenue
9. ✅ Language toggle (EN / हि / HG) works
10. ✅ Dark mode toggle persists after page reload

---

## PRODUCTION DEPLOYMENT (PostgreSQL + Gunicorn)

```bash
# 1. Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/vayapaar
FLASK_ENV=production

# 2. Install production server
pip install gunicorn

# 3. Run
gunicorn "app:app" --workers 4 --bind 0.0.0.0:8000

# 4. Recommended: put Nginx in front of Gunicorn
# 5. Set SECRET_KEY to a truly random 64-char value — never use the default
```

---

## SECURITY CHECKLIST BEFORE GOING LIVE

- [ ] Change `SECRET_KEY` to a random 64-char hex string
- [ ] Set `FLASK_ENV=production` (disables debug mode + detailed tracebacks)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS (Let's Encrypt / Cloudflare)
- [ ] Replace simulated SMTP in `auth.py` with real email (Flask-Mail / SendGrid)
- [ ] Set `SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_HTTPONLY=True` in config
- [ ] Add rate limiting to `/auth/login` (Flask-Limiter: 10 requests/minute)
- [ ] Store `static/uploads/` on S3 or equivalent object storage
- [ ] Run `pip audit` to check for known CVEs in dependencies

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
from models import db, User
from config import config
from translations import TRANSLATIONS
from datetime import datetime


def create_app(env='default'):
    app = Flask(__name__)
    app.config.from_object(config[env])

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(uid)

    # ── CSRF: exempt JSON API routes ──────────────────────────────────────────
    # We handle CSRF manually for fetch() calls via the X-CSRFToken header pattern.
    # Flask-WTF is only used for form-based routes; API blueprint is exempt.
    try:
        from flask_wtf.csrf import CSRFProtect, CSRFError
        csrf = CSRFProtect(app)

        # Exempt the entire /api/* prefix from CSRF (uses JSON + Bearer pattern)
        @app.after_request
        def set_csrf_cookie(response):
            # Expose CSRF token to JS
            from flask_wtf.csrf import generate_csrf
            response.set_cookie('csrf_token', generate_csrf(), samesite='Strict')
            return response

        @app.errorhandler(CSRFError)
        def handle_csrf(e):
            flash('Security token expired. Please try again.', 'error')
            return redirect(request.referrer or url_for('index'))

        # Exempt api blueprint after it is registered (done below)
        app._csrf = csrf
    except ImportError:
        app._csrf = None

    # ── Context processor ─────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        lang = session.get('lang', 'en')
        t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
        return dict(
            t=t,
            lang=lang,
            now=datetime.utcnow(),
            current_year=datetime.utcnow().year,
        )

    # ── Register Blueprints ───────────────────────────────────────────────────
    from blueprints.auth      import auth_bp
    from blueprints.dashboard import dash_bp
    from blueprints.inventory import inv_bp
    from blueprints.pos       import pos_bp
    from blueprints.finance   import fin_bp
    from blueprints.customers import cust_bp
    from blueprints.api       import api_bp
    from blueprints.settings  import settings_bp

    app.register_blueprint(auth_bp,     url_prefix='/auth')
    app.register_blueprint(dash_bp,     url_prefix='/dashboard')
    app.register_blueprint(inv_bp,      url_prefix='/inventory')
    app.register_blueprint(pos_bp,      url_prefix='/pos')
    app.register_blueprint(fin_bp,      url_prefix='/finance')
    app.register_blueprint(cust_bp,     url_prefix='/customers')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp,      url_prefix='/api')

    # Exempt API blueprint from CSRF after registration
    if app._csrf:
        app._csrf.exempt(api_bp)

    # ── Root routes ───────────────────────────────────────────────────────────
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    @app.route('/lang/<code>')
    def set_lang(code):
        if code in ('en', 'hi', 'hinglish'):
            session['lang'] = code
        return redirect(request.referrer or url_for('index'))

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # ── Create tables ─────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_demo_data(app)

    return app


def _seed_demo_data(app):
    """Only seeds if DB is empty — safe to call on every startup."""
    from models import Tenant, User
    if User.query.first():
        return
    # No seeding needed — users self-register


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

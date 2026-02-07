import os
import logging
import traceback

from flask import Flask, redirect, url_for, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

_startup_errors = []


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads")), exist_ok=True)

    # HTTPS support behind Render's proxy
    if os.environ.get("RENDER"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)

    # Gzip compression — typically 60-80% smaller HTML/JSON responses
    from flask_compress import Compress
    Compress(app)

    from app.auth.routes import auth_bp
    from app.assessment.routes import assessment_bp
    from app.dashboard.routes import dashboard_bp
    from app.review.routes import review_bp
    from app.chat.routes import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(chat_bp)

    @app.route("/health")
    def health():
        """Health check — shows app status and config for debugging."""
        import json
        ai_key = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
        db_url = app.config["SQLALCHEMY_DATABASE_URI"]
        db_type = db_url.split("://")[0] if "://" in db_url else "sqlite"
        try:
            import anthropic
            anthropic_installed = True
        except ImportError:
            anthropic_installed = False

        # Test actual DB connection and check tables
        db_ok = False
        db_error = None
        tables = []
        try:
            from sqlalchemy import inspect, text
            db.session.execute(text("SELECT 1"))
            db_ok = True
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
        except Exception as e:
            db_error = str(e)

        return json.dumps({
            "status": "ok" if db_ok else "db_error",
            "ai_key_set": ai_key,
            "anthropic_installed": anthropic_installed,
            "database_type": db_type,
            "database_connected": db_ok,
            "database_error": db_error,
            "tables": tables,
            "startup_errors": _startup_errors,
        }), 200, {"Content-Type": "application/json"}

    # Error handler for file too large (413) — iPad/mobile friendly
    @app.errorhandler(413)
    def file_too_large(error):
        max_mb = app.config.get("MAX_CONTENT_LENGTH", 0) // (1024 * 1024)
        from flask import flash
        flash(f"File too large. Maximum size is {max_mb} MB.", "danger")
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        return redirect(url_for("dashboard.index"))

    # Error handler for 500 errors — show useful info on Render
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except Exception:
            pass
        # Get the original exception if available
        try:
            original = getattr(error, 'original_exception', None) or getattr(error, 'description', error)
            error_detail = f"{type(original).__name__}: {original}" if original != error else str(error)
            tb = traceback.format_exc()
        except Exception:
            error_detail = "Unknown error"
            tb = ""
        logger.error(f"500 error: {error_detail}\n{tb}")
        # Use plain string formatting to avoid any Jinja2 issues in the error handler
        from markupsafe import escape
        safe_detail = escape(error_detail)
        safe_tb = escape(tb) if tb and tb != "NoneType: None\n" else ""
        html = f"""<!DOCTYPE html>
        <html><head><title>Error</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head><body class="bg-light">
        <div class="container py-5">
            <div class="card border-danger">
                <div class="card-header bg-danger text-white"><h5 class="mb-0">Server Error</h5></div>
                <div class="card-body">
                    <p>Something went wrong. The error has been logged.</p>
                    <p class="text-muted small mb-2"><strong>Error:</strong> {safe_detail}</p>
                    {"<pre class='text-muted small' style='white-space:pre-wrap;max-height:300px;overflow:auto'>" + str(safe_tb) + "</pre>" if safe_tb else ""}
                    <p class="text-muted small">Check <a href="/health">/health</a> to verify database connectivity.</p>
                    <a href="/" class="btn btn-primary mt-2">Go to Dashboard</a>
                    <a href="/health" class="btn btn-outline-secondary mt-2">Check Health</a>
                </div>
            </div>
        </div></body></html>"""
        return html, 500

    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified.")
        except Exception as e:
            msg = f"db.create_all() failed: {e}"
            logger.error(msg)
            _startup_errors.append(msg)

        try:
            _safe_migrate()
        except Exception as e:
            msg = f"_safe_migrate() failed: {e}"
            logger.error(msg)
            _startup_errors.append(msg)

        try:
            _seed_admin()
        except Exception as e:
            msg = f"_seed_admin() failed: {e}"
            logger.error(msg)
            _startup_errors.append(msg)

    return app


def _safe_migrate():
    """Add any missing columns / fix column sizes for existing tables."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    is_postgres = "postgresql" in str(db.engine.url)

    # Add must_change_password column if missing
    if "users" in table_names:
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "must_change_password" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE"))
            db.session.commit()

    # Widen fiscal_year from varchar(20) to varchar(100) — values like
    # "FY2025 (ending March 2026)" are 26 chars, exceeding the old limit.
    # SQLite ignores length constraints so only PostgreSQL needs this.
    if is_postgres and "assessments" in table_names:
        cols = {c["name"]: c for c in inspector.get_columns("assessments")}
        fy_col = cols.get("fiscal_year")
        if fy_col and hasattr(fy_col["type"], "length") and (fy_col["type"].length or 0) < 100:
            db.session.execute(text("ALTER TABLE assessments ALTER COLUMN fiscal_year TYPE VARCHAR(100)"))
            db.session.commit()


def _seed_admin():
    """Create default admin user if none exists."""
    from app.models import User

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            full_name="Administrator",
            must_change_password=False,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

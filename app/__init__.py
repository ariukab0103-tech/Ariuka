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

    # Error handler for 500 errors — show useful info on Render
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except Exception:
            pass
        # Get the original exception if available
        original = getattr(error, 'original_exception', None) or getattr(error, 'description', error)
        error_detail = f"{type(original).__name__}: {original}" if original != error else str(error)
        logger.error(f"500 error: {error_detail}\n{traceback.format_exc()}")
        return render_template_string("""
        <!DOCTYPE html>
        <html><head><title>Error</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head><body class="bg-light">
        <div class="container py-5">
            <div class="card border-danger">
                <div class="card-header bg-danger text-white"><h5 class="mb-0">Server Error</h5></div>
                <div class="card-body">
                    <p>Something went wrong. The error has been logged.</p>
                    <p class="text-muted small mb-2"><strong>Error:</strong> {{ error_detail }}</p>
                    <p class="text-muted small">Check <a href="/health">/health</a> to verify database connectivity.</p>
                    <a href="/" class="btn btn-primary mt-2">Go to Dashboard</a>
                    <a href="/health" class="btn btn-outline-secondary mt-2">Check Health</a>
                </div>
            </div>
        </div></body></html>
        """, error_detail=error_detail), 500

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
    """Add any missing columns to existing tables (SQLAlchemy create_all doesn't do this)."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    # Add must_change_password column if missing
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "must_change_password" not in columns:
            # Use DEFAULT FALSE for PostgreSQL compatibility (also works on SQLite)
            db.session.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE"))
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

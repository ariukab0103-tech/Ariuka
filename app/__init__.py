import os

from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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
        try:
            import anthropic
            anthropic_installed = True
        except ImportError:
            anthropic_installed = False
        return json.dumps({
            "status": "ok",
            "ai_key_set": ai_key,
            "anthropic_installed": anthropic_installed,
            "database": app.config["SQLALCHEMY_DATABASE_URI"].split("://")[0] if "://" in app.config["SQLALCHEMY_DATABASE_URI"] else "sqlite",
        }), 200, {"Content-Type": "application/json"}

    with app.app_context():
        db.create_all()
        _safe_migrate()
        _seed_admin()

    return app


def _safe_migrate():
    """Add any missing columns to existing tables (SQLAlchemy create_all doesn't do this)."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    # Add must_change_password column if missing
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "must_change_password" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
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

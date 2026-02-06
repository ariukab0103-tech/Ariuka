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

    # Force password change for users who still have default/temporary passwords
    @app.before_request
    def check_password_change():
        if (
            current_user.is_authenticated
            and current_user.must_change_password
            and request.endpoint not in ("auth.change_password", "auth.logout", "static")
        ):
            return redirect(url_for("auth.change_password"))

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create default admin user if none exists."""
    from app.models import User

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            full_name="Administrator",
            must_change_password=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

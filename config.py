import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database: use DATABASE_URL from environment (PostgreSQL on Render), fallback to SQLite for local dev
    _db_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'ssbj_gap.db')}")
    # Render/Heroku give postgres:// but SQLAlchemy requires postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL connection pooling for speed
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,       # verify connections before using
        "pool_recycle": 300,         # recycle connections every 5 min
        "pool_size": 5,              # keep 5 connections ready
        "max_overflow": 10,          # allow 10 extra under load
    } if "DATABASE_URL" in os.environ else {}
    UPLOAD_FOLDER = os.path.join(basedir, "instance", "uploads")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "csv", "png", "jpg", "jpeg", "txt"}

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour session timeout

    # In production (Render), these are set via HTTPS proxy
    SESSION_COOKIE_SECURE = os.environ.get("RENDER", "") != ""  # True on Render
    PREFERRED_URL_SCHEME = "https" if os.environ.get("RENDER", "") else "http"

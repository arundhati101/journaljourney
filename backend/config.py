import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class Config:
    # In production always set SECRET_KEY in the environment. The random
    # fallback keeps dev working but invalidates sessions on every restart.
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)

    # Default to a local SQLite file, but allow overriding with any SQLAlchemy
    # URL (e.g. a PostgreSQL DSN) so the same code runs in production.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'

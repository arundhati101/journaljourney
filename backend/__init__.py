import os
import ssl
import truststore
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from .config import Config

ssl._create_default_https_context = ssl._create_unverified_context
truststore.inject_into_ssl()

db = SQLAlchemy()
bcrypt = Bcrypt()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
        static_folder=os.path.join(BASE_DIR, 'frontend', 'static'),
    )
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)

    from .routes.auth import auth_bp
    from .routes.journal import journal_bp
    from .routes.dashboard import dashboard_bp
    from .routes.insights import insights_bp
    from .routes.export import export_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)

    _register_error_handlers(app)

    with app.app_context():
        _ensure_schema()
        _backfill_sentiment_scores()

    return app


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify(error='Not found'), 404
        return render_template('error.html', code=404,
                               message="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify(error='Internal server error'), 500
        return render_template('error.html', code=500,
                               message="Something went wrong on our end."), 500


def _ensure_schema():
    from . import models  # noqa: F401 — registers models with SQLAlchemy
    db.create_all()

    # Migration-safe: add columns introduced after the original schema to any
    # pre-existing site.db. db.create_all() never alters existing tables.
    inspector = db.inspect(db.engine)
    existing = {col['name'] for col in inspector.get_columns('diary_entry')}
    new_columns = {
        'sentiment_score': 'FLOAT',
        'emotion': 'VARCHAR(20)',
        'tags': 'VARCHAR(200)',
    }
    for name, coltype in new_columns.items():
        if name not in existing:
            with db.engine.begin() as conn:
                conn.execute(db.text(f'ALTER TABLE diary_entry ADD COLUMN {name} {coltype}'))


def _backfill_sentiment_scores():
    from .models import DiaryEntry
    from .nlp import score_text

    legacy = DiaryEntry.query.filter(DiaryEntry.sentiment_score.is_(None)).all()
    if not legacy:
        return
    for entry in legacy:
        entry.sentiment_score = score_text(entry.text)
    db.session.commit()

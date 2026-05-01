"""
AirSense Backend - Flask Application Factory
"""

from flask import Flask
from .extensions import db, cors
from .routes.ingest import ingest_bp
from .routes.api    import api_bp
from .routes.web    import web_bp


def create_app(config_name="development"):
    app = Flask(__name__, template_folder="../web/templates",
                static_folder="../web/static")

    # ── Configuracion ──────────────────────────────────────────────────────
    app.config.from_object(f"backend.config.{config_name.capitalize()}Config")

    # ── Extensiones ────────────────────────────────────────────────────────
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Blueprints ─────────────────────────────────────────────────────────
    app.register_blueprint(ingest_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # ── Crear tablas si no existen ─────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app

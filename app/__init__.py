"""
Flask application factory.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import get_settings


def create_app() -> Flask:
    """Create and configure Flask application instance."""
    app = Flask(__name__)
    settings = get_settings()

    # Configure Flask
    app.config['SECRET_KEY'] = settings.FLASK_SECRET_KEY
    app.config['ENV'] = settings.FLASK_ENV

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.api import auth, catalog, requests, proposals, admin, health

    app.register_blueprint(auth.bp, url_prefix="/api")
    app.register_blueprint(catalog.bp, url_prefix="/api")
    app.register_blueprint(requests.bp, url_prefix="/api")
    app.register_blueprint(proposals.bp, url_prefix="/api")
    app.register_blueprint(admin.bp, url_prefix="/api")
    app.register_blueprint(health.bp, url_prefix="/api")

    # Register error handlers
    from app.middleware.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "name": "CatalogAI API",
            "version": "0.1.0",
            "status": "running"
        })

    return app

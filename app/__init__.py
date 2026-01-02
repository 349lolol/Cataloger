"""
Flask application factory.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import get_settings
import logging

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


def create_app() -> Flask:
    """Create and configure Flask application instance."""
    app = Flask(__name__)
    settings = get_settings()

    # Configure Flask
    app.config['SECRET_KEY'] = settings.FLASK_SECRET_KEY
    app.config['ENV'] = settings.FLASK_ENV

    # Configure structured logging
    setup_logging(app)

    # Enable CORS with configurable origins
    # Issue #4.2: Properly trim whitespace from comma-separated origins
    if settings.CORS_ORIGINS != "*":
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(',') if o.strip()]
    else:
        origins = "*"
    CORS(app, resources={r"/api/*": {"origins": origins}})

    # Initialize rate limiter (optional)
    try:
        from app.middleware.rate_limiter import init_limiter
        limiter = init_limiter(app)
        app.limiter = limiter
        app.logger.info("Rate limiting enabled")
    except ImportError:
        app.logger.warning("Flask-Limiter not installed - rate limiting disabled")
        app.limiter = None

    # Initialize monitoring (optional)
    try:
        from app.middleware.monitoring import init_monitoring
        init_monitoring(app)
    except ImportError:
        app.logger.warning("OpenTelemetry not installed - monitoring disabled")

    # Register request/response logging middleware (optional)
    try:
        from app.middleware.logging_middleware import register_logging_middleware
        register_logging_middleware(app)
    except ImportError:
        app.logger.warning("Logging middleware disabled")

    # Register blueprints
    from app.api import auth, catalog, requests, proposals, admin, health, products

    app.register_blueprint(auth.bp, url_prefix="/api")
    app.register_blueprint(catalog.bp, url_prefix="/api")
    app.register_blueprint(requests.bp, url_prefix="/api")
    app.register_blueprint(proposals.bp, url_prefix="/api")
    app.register_blueprint(admin.bp, url_prefix="/api")
    app.register_blueprint(health.bp, url_prefix="/api")
    app.register_blueprint(products.bp, url_prefix="/api")

    # Register error handlers
    from app.middleware.error_responses import register_error_handlers
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


def setup_logging(app):
    """Configure structured JSON logging for production."""
    if app.config['ENV'] == 'production' and HAS_JSON_LOGGER:
        # Use JSON logging for production
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        app.logger.addHandler(logHandler)
        app.logger.setLevel(logging.INFO)
    else:
        # Use simple logging for development
        logging.basicConfig(level=logging.DEBUG)

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
    app = Flask(__name__)
    settings = get_settings()

    app.config['SECRET_KEY'] = settings.FLASK_SECRET_KEY
    app.config['ENV'] = settings.FLASK_ENV

    setup_logging(app)

    if settings.CORS_ORIGINS != "*":
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(',') if o.strip()]
    else:
        origins = "*"
    CORS(app, resources={r"/api/*": {"origins": origins}})

    try:
        from app.middleware.rate_limiter import init_limiter
        limiter = init_limiter(app)
        app.limiter = limiter
    except ImportError:
        app.limiter = None

    try:
        from app.middleware.monitoring import init_monitoring
        init_monitoring(app)
    except ImportError:
        pass

    try:
        from app.middleware.logging_middleware import register_logging_middleware
        register_logging_middleware(app)
    except ImportError:
        pass

    from app.api import auth, catalog, requests, proposals, admin, health, products

    app.register_blueprint(auth.bp, url_prefix="/api")
    app.register_blueprint(catalog.bp, url_prefix="/api")
    app.register_blueprint(requests.bp, url_prefix="/api")
    app.register_blueprint(proposals.bp, url_prefix="/api")
    app.register_blueprint(admin.bp, url_prefix="/api")
    app.register_blueprint(health.bp, url_prefix="/api")
    app.register_blueprint(products.bp, url_prefix="/api")

    from app.middleware.error_responses import register_error_handlers
    register_error_handlers(app)

    @app.route('/')
    def index():
        return jsonify({
            "name": "CatalogAI API",
            "version": "0.1.0",
            "status": "running"
        })

    return app


def setup_logging(app):
    if app.config['ENV'] == 'production' and HAS_JSON_LOGGER:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

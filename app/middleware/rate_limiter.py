from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)


def get_user_identifier():
    from flask import g

    if hasattr(g, 'user_id') and g.user_id:
        return f"user:{g.user_id}"

    return f"ip:{get_remote_address()}"


def init_limiter(app: Flask) -> Limiter:
    limiter = Limiter(
        key_func=get_user_identifier,
        app=app,
        default_limits=["200 per minute", "1000 per hour"],
        storage_uri="memory://",
        strategy="fixed-window",
        headers_enabled=True,
    )

    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"Rate limit exceeded: {get_user_identifier()}")
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": e.description
        }), 429

    _apply_endpoint_limits(limiter)

    return limiter


def _apply_endpoint_limits(limiter: Limiter):
    limiter.limit("10 per minute")(
        lambda: request.endpoint == 'products.enrich_product'
    )

    limiter.limit("5 per minute")(
        lambda: request.endpoint == 'products.enrich_batch'
    )

    limiter.limit("30 per minute")(
        lambda: request.endpoint == 'catalog.search_items'
    )

    limiter.limit("10 per minute")(
        lambda: request.endpoint == 'catalog.request_new_item'
    )


def rate_limit(limit_string: str):
    def decorator(f):
        from flask import current_app
        if hasattr(current_app, 'limiter') and current_app.limiter:
            return current_app.limiter.limit(limit_string)(f)
        return f
    return decorator

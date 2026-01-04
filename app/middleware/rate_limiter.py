"""
Rate limiting middleware using Flask-Limiter.

Protects expensive endpoints (especially Gemini API calls) from abuse.
Uses in-memory storage by default, can be configured for Redis in production.
"""
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)


def get_user_identifier():
    """
    Get rate limit key based on user identity.

    Priority:
    1. Authenticated user ID (from JWT)
    2. Remote IP address (fallback)

    This ensures authenticated users get their own rate limit bucket,
    while unauthenticated requests are limited by IP.
    """
    from flask import g

    # If user is authenticated, use their user_id
    if hasattr(g, 'user_id') and g.user_id:
        return f"user:{g.user_id}"

    # Fallback to IP address
    return f"ip:{get_remote_address()}"


def init_limiter(app: Flask) -> Limiter:
    """
    Initialize Flask-Limiter with default rate limits.

    Default limits (can be overridden per-endpoint):
    - 100 requests/minute for general API
    - 10 requests/minute for expensive Gemini endpoints

    Args:
        app: Flask application instance

    Returns:
        Configured Limiter instance
    """
    limiter = Limiter(
        key_func=get_user_identifier,
        app=app,
        default_limits=["200 per minute", "1000 per hour"],
        storage_uri="memory://",  # Use Redis URI in production
        strategy="fixed-window",
        headers_enabled=True,  # Add X-RateLimit headers to responses
    )

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"Rate limit exceeded: {get_user_identifier()}")
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description),
            "retry_after": e.description
        }), 429

    # Apply stricter limits to expensive endpoints
    _apply_endpoint_limits(limiter)

    logger.info("Rate limiter initialized with default limits: 200/min, 1000/hour")
    return limiter


def _apply_endpoint_limits(limiter: Limiter):
    """
    Apply custom rate limits to specific endpoints.

    Expensive operations (Gemini API calls) get stricter limits
    to prevent API quota exhaustion and budget overruns.
    """
    # Product enrichment - expensive Gemini calls
    limiter.limit("10 per minute")(
        lambda: request.endpoint == 'products.enrich_product'
    )

    limiter.limit("5 per minute")(
        lambda: request.endpoint == 'products.enrich_batch'
    )

    # Semantic search - moderate cost (embedding generation)
    limiter.limit("30 per minute")(
        lambda: request.endpoint == 'catalog.search_items'
    )

    # Request new item with AI - includes enrichment
    limiter.limit("10 per minute")(
        lambda: request.endpoint == 'catalog.request_new_item'
    )


# Decorator for applying limits in blueprints
def rate_limit(limit_string: str):
    """
    Decorator to apply rate limit to a specific endpoint.

    Usage:
        @bp.route('/expensive-operation')
        @rate_limit("5 per minute")
        def expensive_operation():
            ...

    Args:
        limit_string: Rate limit specification (e.g., "10 per minute")

    Returns:
        Decorator function
    """
    def decorator(f):
        from flask import current_app
        if hasattr(current_app, 'limiter') and current_app.limiter:
            return current_app.limiter.limit(limit_string)(f)
        return f
    return decorator

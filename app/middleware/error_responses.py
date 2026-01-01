"""
Structured error handling with sanitized responses.
Prevents information disclosure while maintaining debuggability.
"""
from typing import Dict, Optional, Tuple
from flask import jsonify
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error with structured response."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class BadRequestError(AppError):
    """400 - Client provided invalid input."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 400, "BAD_REQUEST", details)


class UnauthorizedError(AppError):
    """401 - Authentication required or failed."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, 401, "UNAUTHORIZED")


class ForbiddenError(AppError):
    """403 - User lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403, "FORBIDDEN")


class NotFoundError(AppError):
    """404 - Resource not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, 404, "NOT_FOUND", {"resource": resource})


class ConflictError(AppError):
    """409 - Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 409, "CONFLICT", details)


class RateLimitExceededError(AppError):
    """429 - Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED")


class ExternalServiceError(AppError):
    """502 - External service (Gemini, Supabase) failed."""

    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            message, 502, "EXTERNAL_SERVICE_ERROR", {"service": service}
        )


class DatabaseError(AppError):
    """503 - Database operation failed."""

    def __init__(self, message: str = "Database operation failed"):
        # Don't expose database details
        super().__init__("Database temporarily unavailable", 503, "DATABASE_ERROR")
        # Log the real error for debugging
        logger.error(f"Database error: {message}")


def format_error_response(error: AppError) -> Tuple[Dict, int]:
    """
    Format AppError into JSON response.

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "error": {
            "code": error.error_code,
            "message": error.message,
        }
    }

    # Include details if available (only for 4xx errors)
    if error.details and 400 <= error.status_code < 500:
        response["error"]["details"] = error.details

    return response, error.status_code


def handle_generic_exception(e: Exception) -> Tuple[Dict, int]:
    """
    Handle unexpected exceptions with sanitized response.
    Logs full error for debugging but returns safe message to client.

    Args:
        e: The caught exception

    Returns:
        Tuple of (response_dict, status_code)
    """
    # Log the full exception for debugging
    logger.exception(f"Unhandled exception: {str(e)}")

    # Return sanitized error to client
    return {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred. Please try again later.",
        }
    }, 500


def register_error_handlers(app):
    """
    Register error handlers with Flask app.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(AppError)
    def handle_app_error(error):
        response, status_code = format_error_response(error)
        return jsonify(response), status_code

    @app.errorhandler(Exception)
    def handle_exception(error):
        response, status_code = handle_generic_exception(error)
        return jsonify(response), status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found"
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "HTTP method not allowed for this endpoint"
            }
        }), 405

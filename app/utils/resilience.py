"""
Resilience utilities: retry logic, circuit breakers, timeouts.
Improves reliability when calling external services.
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from app.config import get_settings
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def safe_int(value: Any, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    Safely convert a value to int with bounds checking.

    Args:
        value: Value to convert (can be str, int, None, etc.)
        default: Default value if conversion fails
        min_val: Optional minimum allowed value
        max_val: Optional maximum allowed value

    Returns:
        Converted integer within bounds, or default on failure

    Example:
        limit = safe_int(request.args.get('limit'), default=100, min_val=1, max_val=1000)
    """
    try:
        result = int(value) if value is not None else default
    except (ValueError, TypeError):
        result = default

    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val

    return result


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID format, False otherwise

    Example:
        if not is_valid_uuid(item_id):
            return jsonify({"error": "Invalid item ID format"}), 400
    """
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(str(value))) if value else False


def validate_metadata(metadata: Any, max_keys: int = 50, max_size_bytes: int = 65536) -> tuple[bool, str]:
    """
    Validate metadata dict for size and structure constraints.

    Args:
        metadata: Metadata dict to validate
        max_keys: Maximum number of keys allowed (default: 50)
        max_size_bytes: Maximum JSON size in bytes (default: 64KB)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_metadata(data.get('metadata'))
        if not valid:
            return jsonify({"error": error}), 400
    """
    import json

    if metadata is None:
        return True, ""

    if not isinstance(metadata, dict):
        return False, "metadata must be a dictionary"

    if len(metadata) > max_keys:
        return False, f"metadata cannot have more than {max_keys} keys"

    try:
        serialized = json.dumps(metadata)
        if len(serialized.encode('utf-8')) > max_size_bytes:
            return False, f"metadata size exceeds maximum of {max_size_bytes} bytes"
    except (TypeError, ValueError) as e:
        return False, f"metadata must be JSON serializable: {str(e)}"

    return True, ""


settings = get_settings()


# Circuit breakers for external services
class ServiceCircuitBreakers:
    """Circuit breakers for external service calls."""

    def __init__(self):
        fail_max = settings.CIRCUIT_BREAKER_FAIL_MAX
        timeout = settings.CIRCUIT_BREAKER_TIMEOUT

        # Gemini API circuit breaker
        self.gemini = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=timeout,
            name="gemini_api"
        )

        # Supabase circuit breaker
        self.supabase = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=timeout,
            name="supabase"
        )

        # Redis circuit breaker
        self.redis = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=timeout,
            name="redis"
        )


# Global circuit breakers instance
_breakers = None


def get_circuit_breakers() -> ServiceCircuitBreakers:
    """Get singleton circuit breakers instance."""
    global _breakers
    if _breakers is None:
        _breakers = ServiceCircuitBreakers()
    return _breakers


# Retry decorators for different failure scenarios

def retry_on_connection_error(max_attempts: int = 3):
    """
    Retry decorator for connection errors with exponential backoff.

    Usage:
        @retry_on_connection_error(max_attempts=5)
        def call_external_api():
            ...

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def retry_on_rate_limit(max_attempts: int = 5):
    """
    Retry decorator for rate limit errors with longer backoff.

    Usage:
        @retry_on_rate_limit(max_attempts=5)
        def call_gemini_api():
            ...

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type((Exception,)),  # Customize based on API errors
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def with_circuit_breaker(breaker_name: str):
    """
    Decorator to wrap function calls with circuit breaker.

    Usage:
        @with_circuit_breaker("gemini")
        def call_gemini_api():
            ...

    Args:
        breaker_name: Name of circuit breaker ("gemini", "supabase", "redis")

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            breakers = get_circuit_breakers()
            breaker = getattr(breakers, breaker_name)

            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                logger.error(f"Circuit breaker {breaker_name} is open - service unavailable")
                raise Exception(f"{breaker_name.capitalize()} service temporarily unavailable")

        return wrapper
    return decorator


# Combined decorators for common patterns

def resilient_external_call(breaker_name: str, max_retries: int = 3):
    """
    Combined decorator for resilient external API calls.
    Includes both retry logic and circuit breaker.

    Usage:
        @resilient_external_call("gemini", max_retries=5)
        def call_gemini_api():
            ...

    Args:
        breaker_name: Circuit breaker to use
        max_retries: Maximum retry attempts

    Returns:
        Decorator function

    Decorator Order:
        retry(circuit_breaker(func)) - Circuit breaker is innermost,
        so failed calls count toward the breaker. Retries happen outside,
        allowing recovery attempts before the breaker opens.
    """
    def decorator(func: Callable) -> Callable:
        # Issue #41: Correct order - circuit breaker innermost, retry outermost
        # This ensures: 1) failures count toward breaker, 2) retries can recover
        wrapped = with_circuit_breaker(breaker_name)(func)
        wrapped = retry_on_connection_error(max_retries)(wrapped)
        return wrapped
    return decorator

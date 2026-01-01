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
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)
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
            timeout_duration=timeout,
            name="gemini_api"
        )

        # Supabase circuit breaker
        self.supabase = CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout,
            name="supabase"
        )

        # Redis circuit breaker
        self.redis = CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout,
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
    """
    def decorator(func: Callable) -> Callable:
        # Apply decorators in order: circuit breaker -> retry -> function
        func = retry_on_connection_error(max_retries)(func)
        func = with_circuit_breaker(breaker_name)(func)
        return func
    return decorator

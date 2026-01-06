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
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(str(value))) if value else False


def require_valid_uuid(value: str, field_name: str = "ID") -> None:
    """Validate UUID format and raise BadRequestError if invalid."""
    from app.middleware.error_responses import BadRequestError
    if not is_valid_uuid(value):
        raise BadRequestError(f"Invalid {field_name} format")


def check_org_access(resource: dict, org_id: str, resource_name: str = "resource") -> None:
    """Check if resource belongs to org and raise ForbiddenError if not."""
    from app.middleware.error_responses import ForbiddenError
    if resource.get('org_id') != org_id:
        raise ForbiddenError(f"Access denied to {resource_name}")


def validate_metadata(metadata: Any, max_keys: int = 50, max_size_bytes: int = 65536) -> tuple[bool, str]:
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


_settings = None


def _get_settings():
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


class ServiceCircuitBreakers:
    def __init__(self):
        settings = _get_settings()
        fail_max = settings.CIRCUIT_BREAKER_FAIL_MAX
        timeout = settings.CIRCUIT_BREAKER_TIMEOUT

        self.gemini = CircuitBreaker(fail_max=fail_max, reset_timeout=timeout, name="gemini_api")
        self.supabase = CircuitBreaker(fail_max=fail_max, reset_timeout=timeout, name="supabase")
        self.redis = CircuitBreaker(fail_max=fail_max, reset_timeout=timeout, name="redis")


_breakers = None


def get_circuit_breakers() -> ServiceCircuitBreakers:
    global _breakers
    if _breakers is None:
        _breakers = ServiceCircuitBreakers()
    return _breakers


def retry_on_connection_error(max_attempts: int = None):
    if max_attempts is None:
        max_attempts = _get_settings().RETRY_MAX_ATTEMPTS
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def retry_on_rate_limit(max_attempts: int = None):
    if max_attempts is None:
        max_attempts = _get_settings().RETRY_RATE_LIMIT_ATTEMPTS
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def with_circuit_breaker(breaker_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            breakers = get_circuit_breakers()
            breaker = getattr(breakers, breaker_name)

            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                logger.error(f"Circuit breaker {breaker_name} is open")
                raise Exception(f"{breaker_name.capitalize()} service temporarily unavailable")

        return wrapper
    return decorator


def resilient_external_call(breaker_name: str, max_retries: int = None):
    def decorator(func: Callable) -> Callable:
        wrapped = with_circuit_breaker(breaker_name)(func)
        wrapped = retry_on_connection_error(max_retries)(wrapped)
        return wrapped
    return decorator

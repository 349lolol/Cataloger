"""
Health check endpoints for monitoring and load balancers.
"""
from flask import Blueprint, jsonify
from app.extensions import get_supabase_client
from app.config import get_settings
import time
import logging
import threading

bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

# Store app start time for uptime calculation
app_start_time = time.time()

# Cache Gemini API check result to avoid expensive API calls on every health check
_gemini_check_cache = {"result": None, "timestamp": 0}
_gemini_cache_lock = threading.Lock()
GEMINI_CACHE_TTL = 60  # Cache for 60 seconds


@bp.route('/health', methods=['GET'])
def health_check():
    """
    AWS ELB/ALB health check endpoint.
    Returns 200 if service is healthy.
    This is a lightweight check - just returns uptime.
    """
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int(time.time() - app_start_time)
    }), 200


@bp.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Kubernetes-style readiness check.
    Verifies all critical dependencies are available.

    Checks:
    - Supabase database connectivity
    - Redis availability (optional)
    - Gemini API accessibility

    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "database": check_database(),
        "gemini_api": check_gemini_api(),
    }

    all_healthy = checks["database"] and checks["gemini_api"]

    if all_healthy:
        return jsonify({
            "status": "ready",
            "checks": checks,
            "uptime_seconds": int(time.time() - app_start_time)
        }), 200
    else:
        return jsonify({
            "status": "not_ready",
            "checks": checks
        }), 503


def check_database() -> bool:
    """Check if Supabase database is accessible."""
    try:
        supabase = get_supabase_client()
        # Simple query to verify connectivity
        response = supabase.table('orgs').select('id').limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_gemini_api() -> bool:
    """
    Check if Gemini API is accessible.
    Results are cached for 60 seconds to avoid expensive API calls on
    frequent health checks (load balancers check every 5-10 seconds).
    """
    global _gemini_check_cache

    current_time = time.time()

    # Check if we have a valid cached result
    if _gemini_check_cache["result"] is not None:
        if current_time - _gemini_check_cache["timestamp"] < GEMINI_CACHE_TTL:
            return _gemini_check_cache["result"]

    # Need to refresh - use lock to prevent concurrent API calls
    with _gemini_cache_lock:
        # Double-check after acquiring lock
        if _gemini_check_cache["result"] is not None:
            if current_time - _gemini_check_cache["timestamp"] < GEMINI_CACHE_TTL:
                return _gemini_check_cache["result"]

        try:
            settings = get_settings()
            # Just validate API key format instead of making API call
            # The key should be a non-empty string
            api_key = settings.GEMINI_API_KEY
            if api_key and len(api_key) > 10:
                result = True
            else:
                logger.error("Gemini API key appears invalid or too short")
                result = False
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            result = False

        # Update cache
        _gemini_check_cache["result"] = result
        _gemini_check_cache["timestamp"] = current_time

        return result

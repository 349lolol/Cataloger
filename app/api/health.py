"""
Health check endpoints for monitoring and load balancers.
"""
from flask import Blueprint, jsonify
from app.extensions import get_supabase_client
from app.config import get_settings
import time
import logging
import google.generativeai as genai

bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

# Store app start time for uptime calculation
app_start_time = time.time()


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
    """Check if Gemini API is accessible."""
    try:
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # List models as a lightweight check
        models = genai.list_models()
        return True
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
        return False

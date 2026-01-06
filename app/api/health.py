from flask import Blueprint, jsonify
from app.extensions import get_supabase_client
from app.config import get_settings
import time
import logging
import threading

bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

app_start_time = time.time()

_gemini_check_cache = {"result": None, "timestamp": 0}
_gemini_cache_lock = threading.Lock()
GEMINI_CACHE_TTL = 60


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int(time.time() - app_start_time)
    }), 200


@bp.route('/readiness', methods=['GET'])
def readiness_check():
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
    try:
        supabase = get_supabase_client()
        supabase.table('orgs').select('id').limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


def check_gemini_api() -> bool:
    global _gemini_check_cache

    current_time = time.time()

    if _gemini_check_cache["result"] is not None:
        if current_time - _gemini_check_cache["timestamp"] < GEMINI_CACHE_TTL:
            return _gemini_check_cache["result"]

    with _gemini_cache_lock:
        if _gemini_check_cache["result"] is not None:
            if current_time - _gemini_check_cache["timestamp"] < GEMINI_CACHE_TTL:
                return _gemini_check_cache["result"]

        try:
            settings = get_settings()
            api_key = settings.GEMINI_API_KEY
            result = bool(api_key and len(api_key) > 10)
        except Exception as e:
            logger.error(f"Gemini check failed: {e}")
            result = False

        _gemini_check_cache["result"] = result
        _gemini_check_cache["timestamp"] = current_time

        return result

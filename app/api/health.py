"""
Health check endpoints for monitoring and load balancers.
"""
from flask import Blueprint, jsonify
import time

bp = Blueprint('health', __name__)

# Store app start time for uptime calculation
app_start_time = time.time()


@bp.route('/health', methods=['GET'])
def health_check():
    """
    AWS ELB/ALB health check endpoint.
    Returns 200 if service is healthy.
    """
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int(time.time() - app_start_time)
    }), 200


@bp.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Kubernetes-style readiness check.
    Could check Supabase connectivity, embedding model loaded, etc.
    """
    # TODO: Add actual readiness checks (database connection, model loaded)
    return jsonify({"status": "ready"}), 200

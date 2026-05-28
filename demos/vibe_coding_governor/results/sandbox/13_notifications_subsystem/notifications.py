"""Notifications subsystem (demo)."""
from flask import Blueprint, jsonify, request

from app import require_auth

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notify", methods=["POST"])
@require_auth
def notify():
    data = request.get_json()
    return jsonify({"queued": data.get("message", "")})

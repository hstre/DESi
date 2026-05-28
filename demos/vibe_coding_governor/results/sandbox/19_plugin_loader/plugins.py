"""Dynamic plugin loader subsystem (demo)."""
import importlib

from flask import Blueprint, jsonify, request

from app import require_auth

plugins_bp = Blueprint("plugins", __name__)


@plugins_bp.route("/plugins/run", methods=["POST"])
@require_auth
def run_plugin():
    data = request.get_json()
    mod = importlib.import_module(data["module"])
    return jsonify({"loaded": getattr(mod, "__name__", "?")})

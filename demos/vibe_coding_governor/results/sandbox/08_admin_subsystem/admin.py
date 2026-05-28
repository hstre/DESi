"""Admin subsystem (demo)."""
import importlib  # noqa: F401

from flask import Blueprint, jsonify, request  # noqa: F401

from app import require_auth
from db import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/users", methods=["GET"])
@require_auth
def admin_users():
    db = get_db()
    cur = db.execute("SELECT id, username FROM users ORDER BY id")
    return jsonify([dict(r) for r in cur.fetchall()])


@admin_bp.route("/admin/stats", methods=["GET"])
@require_auth
def admin_stats():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) AS n FROM todos")
    return jsonify(dict(cur.fetchone()))

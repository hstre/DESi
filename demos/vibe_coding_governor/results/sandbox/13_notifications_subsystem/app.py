"""Minimal todo API (demo). The governor analyses this structurally, not for syntax."""
import logging

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db, run_migrations

app = Flask(__name__)
log = logging.getLogger("todo")


def require_auth(fn):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "")
        if not _valid_token(token):
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


def _valid_token(token):
    return bool(token) and token.startswith("Bearer ")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    db = get_db()
    cur = db.execute("SELECT pw_hash FROM users WHERE username = ?", (data["username"],))
    row = cur.fetchone()
    if row and check_password_hash(row["pw_hash"], data["password"]):
        log.info("login ok for user=%s", data["username"])
        return jsonify({"token": "Bearer demo"})
    return jsonify({"error": "invalid"}), 401


@app.route("/todos", methods=["GET"])
@require_auth
def list_todos():
    db = get_db()
    cur = db.execute("SELECT id, title FROM todos ORDER BY id")
    return jsonify([dict(r) for r in cur.fetchall()])


@app.route("/todos", methods=["POST"])
@require_auth
def add_todo():
    db = get_db()
    data = request.get_json()
    db.execute("INSERT INTO todos (title) VALUES (?)", (data["title"],))
    db.commit()
    return jsonify({"status": "created"}), 201


@app.route("/todos/<int:todo_id>/tag", methods=["POST"])
@require_auth
def set_tag(todo_id):
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE todos SET tag = ? WHERE id = ?", (data["tag"], todo_id))
    db.commit()
    return jsonify({"status": "tagged"})


@app.route("/search", methods=["GET"])
@require_auth
def search():
    db = get_db()
    q = request.args.get("q", "")
    cur = db.execute("SELECT id, title FROM todos WHERE title LIKE ?", ("%" + q + "%",))
    return jsonify([dict(r) for r in cur.fetchall()])


@app.route("/export", methods=["GET"])
@require_auth
def export_csv():
    db = get_db()
    cur = db.execute("SELECT id, title FROM todos ORDER BY id")
    return jsonify({"rows": [dict(r) for r in cur.fetchall()]})


@app.route("/todos/<int:todo_id>/due", methods=["POST"])
@require_auth
def set_due(todo_id):
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE todos SET due_date = ? WHERE id = ?", (data["due_date"], todo_id))
    db.commit()
    return jsonify({"status": "scheduled"})


@app.route("/todos/<int:todo_id>/priority", methods=["POST"])
@require_auth
def set_priority(todo_id):
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE todos SET priority = ? WHERE id = ?", (data["priority"], todo_id))
    db.commit()
    return jsonify({"status": "prioritized"})


@app.route("/reset", methods=["POST"])
@require_auth
def reset_password():
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE users SET pw_hash = ? WHERE username = ?",
               (generate_password_hash(data["password"]), data["username"]))
    db.commit()
    return jsonify({"status": "reset"})


@app.route("/debug", methods=["POST"])
@require_auth
def debug_login():
    data = request.get_json()
    log.info("debug user=%s", data["username"])
    return jsonify({"status": "logged"})

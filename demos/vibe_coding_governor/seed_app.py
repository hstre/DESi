"""The seed app (iteration 0): a tiny, governance-clean Flask + SQLite todo API.

The app itself is NOT the point -- it is just a realistic, valid-Python surface for
the governor to analyse and for the scripted LLM mutations to edit. The seed passes
every governance invariant (auth on all non-public routes, hashed passwords,
parameterized SQL, no secret logging, deterministic migrations, consistent schema).

Sources are held as {filename: source_text}. Mutations return NEW source maps; the
governor decides accept / block / sandbox for each candidate.
"""
from __future__ import annotations

APP_PY = '''\
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
'''

DB_PY = '''\
"""Schema + deterministic migrations for the todo API (demo)."""
import sqlite3

MIGRATIONS = [
    (1, "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, pw_hash TEXT NOT NULL)"),
    (2, "CREATE TABLE todos (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"),
    # <<MIGRATIONS_END>>
]


def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn


def run_migrations(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    applied = {r[0] for r in db.execute("SELECT version FROM schema_version")}
    for version, sql in sorted(MIGRATIONS, key=lambda m: m[0]):
        if version not in applied:
            db.execute(sql)
            db.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    db.commit()
'''


def seed_sources() -> dict:
    return {"app.py": APP_PY, "db.py": DB_PY}

"""Schema + deterministic migrations for the todo API (demo)."""
import sqlite3

MIGRATIONS = [
    (1, "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, pw_hash TEXT NOT NULL)"),
    (2, "CREATE TABLE todos (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"),
    (3, 'ALTER TABLE todos ADD COLUMN tag TEXT'),
    (4, 'ALTER TABLE todos ADD COLUMN due_date TEXT'),
    (5, 'ALTER TABLE todos ADD COLUMN priority INTEGER DEFAULT 0'),
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

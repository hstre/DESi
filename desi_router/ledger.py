"""A local Layer 9 — one shared, append-only ledger for everything DESi does.

Several DESi instances on a machine (or a shared network path) write to the same
SQLite file. Every event is appended, never mutated or deleted, and hash-chained
to its predecessor (Alexandria-style tamper evidence): the chain hash of row N
covers row N's content *and* the chain hash of row N-1, so any later edit to any
past row breaks verification.

Beyond storage, the ledger is what lets an instance ask, before working: *has
this already been done?* — by **content** (the same task/query) or by **method**
(the same routing approach). Those are indexed by ``content_hash`` and
``method_hash``; they are derived metadata for fast lookup and are deliberately
NOT part of the hash chain (the chain covers the canonical event; the indexes are
recomputable from it).

Scope, honestly: this is the *local* substrate — one file, shared by local
instances. It is not the federated, cross-institutional Layer 9 of the working
paper; it is its smallest honest, running form. Concurrency across instances is
handled by SQLite WAL + an IMMEDIATE write transaction (the chain is serialized).

Stdlib only (``sqlite3``).
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq             INTEGER PRIMARY KEY,
    ts              TEXT NOT NULL,
    instance_id     TEXT NOT NULL,
    kind            TEXT NOT NULL,
    decision_hash   TEXT,
    payload         TEXT NOT NULL,
    prev_chain_hash TEXT NOT NULL,
    chain_hash      TEXT NOT NULL,
    content_hash    TEXT DEFAULT '',
    method_hash     TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_dhash ON events(decision_hash);
"""


def default_instance_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _chain(prev_chain_hash: str, core: dict[str, Any]) -> str:
    canonical = json.dumps(core, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((prev_chain_hash + canonical).encode("utf-8")).hexdigest()


class Ledger:
    def __init__(self, path: str | Path, instance_id: str | None = None):
        self.path = str(path)
        self.instance_id = instance_id or default_instance_id()
        self._con = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        self._con.row_factory = sqlite3.Row
        self._con.execute("PRAGMA busy_timeout=30000")
        # WAL is a persistent, file-level mode. Under heavy concurrent first-open
        # (many instances at once) the switch can transiently raise
        # 'database is locked'; retry briefly, then proceed — the mode is a
        # performance optimization, and once any instance sets it the file stays WAL.
        for _attempt in range(100):
            try:
                self._con.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError:
                time.sleep(0.05)
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        cols = {r["name"] for r in self._con.execute("PRAGMA table_info(events)")}
        for col in ("content_hash", "method_hash"):
            if col not in cols:
                self._con.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT DEFAULT ''")
        self._con.execute("CREATE INDEX IF NOT EXISTS idx_events_chash ON events(content_hash)")
        self._con.execute("CREATE INDEX IF NOT EXISTS idx_events_mhash ON events(method_hash)")

    # ---- write (append-only, serialized) ----

    def record(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        decision_hash: str | None = None,
        content_hash: str | None = None,
        method_hash: str | None = None,
    ) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        while True:
            try:
                self._con.execute("BEGIN IMMEDIATE")
                row = self._con.execute(
                    "SELECT seq, chain_hash FROM events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                prev_seq, prev_chain = (row["seq"], row["chain_hash"]) if row else (0, "")
                seq = prev_seq + 1
                core = {
                    "seq": seq, "ts": ts, "instance_id": self.instance_id,
                    "kind": kind, "decision_hash": decision_hash or "", "payload": payload,
                }
                chain_hash = _chain(prev_chain, core)
                self._con.execute(
                    "INSERT INTO events(seq,ts,instance_id,kind,decision_hash,payload,"
                    "prev_chain_hash,chain_hash,content_hash,method_hash)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (seq, ts, self.instance_id, kind, decision_hash or "",
                     json.dumps(payload, ensure_ascii=False), prev_chain, chain_hash,
                     content_hash or "", method_hash or ""),
                )
                self._con.execute("COMMIT")
                return {"seq": seq, "ts": ts, "chain_hash": chain_hash}
            except sqlite3.OperationalError:
                self._con.execute("ROLLBACK")
                continue  # busy: another instance is mid-append; retry

    # ---- read ----

    @staticmethod
    def _to_dict(r: sqlite3.Row) -> dict:
        return {
            "seq": r["seq"], "ts": r["ts"], "instance_id": r["instance_id"],
            "kind": r["kind"], "decision_hash": r["decision_hash"],
            "payload": json.loads(r["payload"]),
            "prev_chain_hash": r["prev_chain_hash"], "chain_hash": r["chain_hash"],
            "content_hash": r["content_hash"], "method_hash": r["method_hash"],
        }

    def all(self, limit: int | None = None, kind: str | None = None) -> list[dict]:
        sql = "SELECT * FROM events"
        args: list[Any] = []
        if kind:
            sql += " WHERE kind=?"
            args.append(kind)
        sql += " ORDER BY seq ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return [self._to_dict(r) for r in self._con.execute(sql, args)]

    def tail(self, n: int = 20) -> list[dict]:
        rows = self._con.execute(
            "SELECT * FROM events ORDER BY seq DESC LIMIT ?", (n,)
        ).fetchall()
        return [self._to_dict(r) for r in reversed(rows)]

    def by_decision_hash(self, decision_hash: str) -> list[dict]:
        return [self._to_dict(r) for r in self._con.execute(
            "SELECT * FROM events WHERE decision_hash=? ORDER BY seq", (decision_hash,))]

    def by_content_hash(self, content_hash: str) -> list[dict]:
        if not content_hash:
            return []
        return [self._to_dict(r) for r in self._con.execute(
            "SELECT * FROM events WHERE content_hash=? ORDER BY seq", (content_hash,))]

    def by_method_hash(self, method_hash: str) -> list[dict]:
        if not method_hash:
            return []
        return [self._to_dict(r) for r in self._con.execute(
            "SELECT * FROM events WHERE method_hash=? ORDER BY seq", (method_hash,))]

    def stats(self) -> dict:
        c = self._con
        count = c.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
        instances = [r["instance_id"] for r in c.execute("SELECT DISTINCT instance_id FROM events")]
        kinds = {r["kind"]: r["n"] for r in c.execute("SELECT kind, COUNT(*) AS n FROM events GROUP BY kind")}
        head = c.execute("SELECT chain_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return {
            "count": count,
            "instances": sorted(instances),
            "kinds": kinds,
            "head_chain_hash": head["chain_hash"] if head else "",
        }

    # ---- integrity ----

    def verify_chain(self) -> bool:
        prev = ""
        for r in self._con.execute("SELECT * FROM events ORDER BY seq ASC"):
            d = self._to_dict(r)
            core = {
                "seq": d["seq"], "ts": d["ts"], "instance_id": d["instance_id"],
                "kind": d["kind"], "decision_hash": d["decision_hash"], "payload": d["payload"],
            }
            if d["prev_chain_hash"] != prev or _chain(prev, core) != d["chain_hash"]:
                return False
            prev = d["chain_hash"]
        return True

    def close(self) -> None:
        self._con.close()


def _cli() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Inspect a local DESi ledger")
    ap.add_argument("path")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--tail", type=int, default=0)
    args = ap.parse_args()
    led = Ledger(args.path, instance_id="cli")
    if args.stats:
        print(json.dumps(led.stats(), indent=2))
    if args.verify:
        print("chain intact:", led.verify_chain())
    if args.tail:
        for e in led.tail(args.tail):
            print(f"#{e['seq']:>5} {e['ts']} {e['instance_id']:>20} {e['kind']:>8} "
                  f"{e['decision_hash'][:12]} {e['chain_hash'][:12]}")
    led.close()


if __name__ == "__main__":
    _cli()

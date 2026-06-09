"""A local Layer 9 — one shared, append-only ledger for everything DESi does.

Several DESi instances on a machine (or a shared network path) write to the same
SQLite file. Every event is appended, never mutated or deleted, and hash-chained
to its predecessor (Alexandria-style tamper evidence): the chain hash of row N
covers row N's content *and* the chain hash of row N-1, so any later edit to any
past row breaks verification.

Scope, honestly: this is the *local* substrate — one file, shared by local
instances. It is not the federated, cross-institutional Layer 9 of the working
paper; it is its smallest honest, running form. Concurrency across instances is
handled by SQLite WAL + an IMMEDIATE write transaction (the chain is serialized).

Stdlib only (``sqlite3``). Queries and answers are stored locally as given —
treat the file as you would any local data store.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
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
    chain_hash      TEXT NOT NULL
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
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.execute("PRAGMA busy_timeout=30000")
        self._con.executescript(_SCHEMA)

    # ---- write (append-only, serialized) ----

    def record(self, kind: str, payload: dict[str, Any], *, decision_hash: str | None = None) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        while True:
            try:
                self._con.execute("BEGIN IMMEDIATE")
                row = self._con.execute(
                    "SELECT seq, chain_hash FROM events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                prev_seq, prev_chain = (row[0], row[1]) if row else (0, "")
                seq = prev_seq + 1
                core = {
                    "seq": seq, "ts": ts, "instance_id": self.instance_id,
                    "kind": kind, "decision_hash": decision_hash or "", "payload": payload,
                }
                chain_hash = _chain(prev_chain, core)
                self._con.execute(
                    "INSERT INTO events(seq,ts,instance_id,kind,decision_hash,payload,prev_chain_hash,chain_hash)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                    (seq, ts, self.instance_id, kind, decision_hash or "",
                     json.dumps(payload, ensure_ascii=False), prev_chain, chain_hash),
                )
                self._con.execute("COMMIT")
                return {"seq": seq, "ts": ts, "chain_hash": chain_hash}
            except sqlite3.OperationalError:
                self._con.execute("ROLLBACK")
                continue  # busy: another instance is mid-append; retry

    # ---- read ----

    def _to_dict(self, r: tuple) -> dict:
        return {
            "seq": r[0], "ts": r[1], "instance_id": r[2], "kind": r[3],
            "decision_hash": r[4], "payload": json.loads(r[5]),
            "prev_chain_hash": r[6], "chain_hash": r[7],
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

    def stats(self) -> dict:
        c = self._con
        count = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        instances = [r[0] for r in c.execute("SELECT DISTINCT instance_id FROM events")]
        kinds = {r[0]: r[1] for r in c.execute("SELECT kind, COUNT(*) FROM events GROUP BY kind")}
        head = c.execute("SELECT chain_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return {
            "count": count,
            "instances": sorted(instances),
            "kinds": kinds,
            "head_chain_hash": head[0] if head else "",
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

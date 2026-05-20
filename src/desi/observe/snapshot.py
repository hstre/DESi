"""GraphSnapshot — frozen view of the memory store at one point in time.

A snapshot captures every Claim, Relation, Run, and OperatorEvent in
the store and exports them as JSON or as a Neo4j-compatible Cypher
script. v0.4 keeps the in-memory snapshot model deliberately simple:
no streaming, no pagination, no diff. The store contents at the moment
of capture are walked once and frozen into immutable lists.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..memory.store import InMemoryStore, MemoryStore


@dataclass(frozen=True)
class GraphSnapshot:
    """Immutable view of a memory store at one moment in time.

    Each list is sorted by a stable key so that two snapshots taken
    over identical store contents compare equal byte-for-byte.
    """

    label: str  # e.g. "start" / "after_branch" / "end"
    tick: int
    claims: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    relations: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    runs: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------
    # Exporters
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "tick": self.tick,
            "counts": {
                "claims": len(self.claims),
                "relations": len(self.relations),
                "runs": len(self.runs),
                "events": len(self.events),
            },
            "claims": list(self.claims),
            "relations": list(self.relations),
            "runs": list(self.runs),
            "events": list(self.events),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    def to_cypher(self) -> str:
        """Emit a Neo4j-compatible Cypher script that recreates the snapshot.

        Statements are MERGE-based so that re-applying a snapshot is
        idempotent, mirroring the migrations module's contract.
        """
        lines: list[str] = []
        lines.append(f"// snapshot label={self.label!r} tick={self.tick}")
        for c in self.claims:
            lines.append(_merge_claim_cypher(c))
        for r in self.runs:
            lines.append(_merge_run_cypher(r))
        for e in self.events:
            lines.append(_merge_event_cypher(e))
        for rel in self.relations:
            lines.append(_merge_relation_cypher(rel))
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def snapshot_store(
    store: MemoryStore,
    *,
    label: str = "snapshot",
    tick: int = 0,
) -> GraphSnapshot:
    """Walk ``store`` and freeze its contents into a :class:`GraphSnapshot`.

    The walk only uses the public protocol surface (``all_claims`` plus
    the recorded run / event accessors); for InMemoryStore that path
    is exhaustive. For Neo4jStore it is exhaustive for claims and
    needs an explicit ``run_id`` for events — the snapshot helper
    therefore records empty events from a Neo4j store when no run id
    list is available, and callers can still re-export the claim/run
    layer for diffing.
    """
    claims = sorted(
        (c.to_record() for c in store.all_claims()),
        key=lambda d: d["claim_id"],
    )
    runs_iter = _iter_runs(store)
    runs_recs = sorted(
        (r.to_record() for r in runs_iter),
        key=lambda d: d["run_id"],
    )
    events_recs: list[dict[str, Any]] = []
    relations_recs: list[dict[str, Any]] = []
    seen_run_ids = [r["run_id"] for r in runs_recs]
    for rid in seen_run_ids:
        for e in store.events_for_run(rid):
            events_recs.append(e.to_record())
    events_recs.sort(key=lambda d: (d.get("run_id", ""),
                                     d.get("loop_index", 0),
                                     d["event_id"]))
    # Relations: pull through the store; for InMemoryStore the
    # protocol exposes them per-claim, so iterate over claim ids.
    relations_internal = getattr(store, "_relations", None)
    if isinstance(relations_internal, list):
        relations_recs = sorted(
            (r.to_record() for r in relations_internal),
            key=lambda d: (d["source_claim_id"],
                            d["rel_type"],
                            d["target_claim_id"]),
        )
    else:
        # Fallback: collect via per-claim relations_for("…", direction="out")
        for cid in (c["claim_id"] for c in claims):
            for r in store.relations_for(cid, direction="out"):
                relations_recs.append(r.to_record())
        relations_recs.sort(
            key=lambda d: (d["source_claim_id"],
                            d["rel_type"],
                            d["target_claim_id"]),
        )
    return GraphSnapshot(
        label=label,
        tick=tick,
        claims=tuple(claims),
        relations=tuple(relations_recs),
        runs=tuple(runs_recs),
        events=tuple(events_recs),
    )


def _iter_runs(store: MemoryStore):
    runs = getattr(store, "_runs", None)
    if isinstance(runs, dict):
        for r in runs.values():
            yield r


# ---------------------------------------------------------------------------
# Cypher emitters
# ---------------------------------------------------------------------------


def _merge_claim_cypher(rec: dict[str, Any]) -> str:
    return (f"MERGE (c:Claim {{claim_id: {_q(rec['claim_id'])}}}) "
            f"SET c += {_props(rec)};")


def _merge_run_cypher(rec: dict[str, Any]) -> str:
    return (f"MERGE (r:Run {{run_id: {_q(rec['run_id'])}}}) "
            f"SET r += {_props(rec)};")


def _merge_event_cypher(rec: dict[str, Any]) -> str:
    return (
        f"MATCH (r:Run {{run_id: {_q(rec['run_id'])}}}) "
        f"MERGE (e:OperatorEvent {{event_id: {_q(rec['event_id'])}}}) "
        f"SET e += {_props(rec)} "
        f"MERGE (r)-[:PRODUCED]->(e);"
    )


def _merge_relation_cypher(rec: dict[str, Any]) -> str:
    rel = rec["rel_type"]
    return (
        f"MATCH (s:Claim {{claim_id: {_q(rec['source_claim_id'])}}}), "
        f"(t:Claim {{claim_id: {_q(rec['target_claim_id'])}}}) "
        f"MERGE (s)-[r:{rel}]->(t) "
        f"SET r.weight = {rec['weight']}, "
        f"r.created_at = {_q(rec['created_at'])};"
    )


def _props(rec: dict[str, Any]) -> str:
    items = ", ".join(f"{k}: {_v(v)}" for k, v in sorted(rec.items()))
    return "{" + items + "}"


def _v(v: Any) -> str:
    if isinstance(v, str):
        return _q(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_v(x) for x in v) + "]"
    if v is None:
        return "null"
    return json.dumps(v)


def _q(s: str) -> str:
    return json.dumps(s)

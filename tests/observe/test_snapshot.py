"""Tests for GraphSnapshot — JSON, Cypher, equality, consistency."""
from __future__ import annotations

import json

from desi.memory import (
    Claim,
    InMemoryStore,
    MemoryRecorder,
    Provenance,
    RelationType,
)
from desi.observe import snapshot_store


def _populate(store: InMemoryStore) -> None:
    rec = MemoryRecorder(store)
    rec.start_run(model="m")
    rec.record_claim(content="alpha", method="T6")
    rec.record_claim(content="beta", method="T6")
    a, b = list(store.all_claims())
    rec.record_relation(source=a, target=b,
                        rel_type=RelationType.SUPPORTS)
    rec.end_run()


def test_snapshot_captures_claims_runs_relations() -> None:
    store = InMemoryStore()
    _populate(store)
    snap = snapshot_store(store, label="t", tick=42)
    assert len(snap.claims) == 2
    assert len(snap.runs) == 1
    assert len(snap.relations) == 1
    assert snap.label == "t"
    assert snap.tick == 42


def test_snapshot_to_dict_has_counts_block() -> None:
    store = InMemoryStore()
    _populate(store)
    snap = snapshot_store(store)
    d = snap.to_dict()
    assert d["counts"] == {"claims": 2, "relations": 1, "runs": 1, "events": 0}


def test_snapshot_to_json_is_parseable() -> None:
    store = InMemoryStore()
    _populate(store)
    snap = snapshot_store(store)
    s = snap.to_json()
    parsed = json.loads(s)
    assert parsed["counts"]["claims"] == 2


def test_two_snapshots_of_same_store_compare_equal() -> None:
    store = InMemoryStore()
    _populate(store)
    a = snapshot_store(store, label="x", tick=1)
    b = snapshot_store(store, label="x", tick=1)
    assert a == b


def test_to_cypher_uses_idempotent_merges() -> None:
    store = InMemoryStore()
    _populate(store)
    snap = snapshot_store(store)
    cy = snap.to_cypher()
    # Each statement should be a MERGE (re-applying is safe).
    statement_lines = [l for l in cy.splitlines()
                       if l and not l.startswith("//")]
    assert all("MERGE" in s for s in statement_lines)


def test_snapshot_after_state_change_differs() -> None:
    store = InMemoryStore()
    _populate(store)
    before = snapshot_store(store, label="before")
    # Add another claim through a fresh recorder.
    rec = MemoryRecorder(store)
    rec.start_run(model="m2")
    rec.record_claim(content="gamma", method="T6")
    rec.end_run()
    after = snapshot_store(store, label="after")
    assert len(before.claims) == 2
    assert len(after.claims) == 3
    assert before != after


def test_snapshot_with_empty_store_is_well_formed() -> None:
    snap = snapshot_store(InMemoryStore(), label="empty")
    d = snap.to_dict()
    assert d["counts"] == {"claims": 0, "relations": 0, "runs": 0, "events": 0}

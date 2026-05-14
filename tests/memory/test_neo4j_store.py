"""Tests for Neo4jStore using a fake driver.

Real Neo4j is not required to run these tests. The fake driver below
implements the subset of the official driver protocol that Neo4jStore
exercises: ``driver.session(database=...)`` returns a context manager
with a ``.run(cypher, **params)`` method that returns a ``Result``
supporting ``.single()`` and iteration. The fake interprets Cypher by
keyword/pattern matching rather than parsing — this couples tests to
the exact Cypher Neo4jStore emits, which is the intended trade-off:
if Neo4jStore changes its Cypher, these tests must be updated.

A separate test in this module verifies that Neo4jStore raises
:class:`Neo4jDriverNotInstalled` when invoked without driver on a host
without the ``neo4j`` package.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

import pytest

from desi.memory import (
    Claim,
    ClaimState,
    Neo4jDriverNotInstalled,
    Neo4jStore,
    OperatorEvent,
    Provenance,
    Relation,
    RelationType,
    Run,
)
from desi.memory import store as store_module


# ---------------------------------------------------------------------------
# Fake driver
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def single(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class _FakeSession:
    def __init__(self, db: "_FakeGraph") -> None:
        self._db = db
        self.queries: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    def run(self, cypher: str, **params: Any) -> _FakeResult:
        self.queries.append((cypher, params))
        return self._db.execute(cypher, params)


class _FakeGraph:
    """Toy in-memory graph that interprets Neo4jStore's Cypher patterns."""

    def __init__(self) -> None:
        self.claims: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}
        # (source_id, rel_type, target_id) -> props
        self.relations: dict[tuple[str, str, str], dict[str, Any]] = {}
        # run_id -> set(event_id) for the PRODUCED edge
        self.run_produced: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    def execute(self, cypher: str, params: dict[str, Any]) -> _FakeResult:
        c = " ".join(cypher.split())

        # MERGE on a Claim node.
        if c.startswith("MERGE (c:Claim "):
            cid = params["claim_id"]
            self.claims.setdefault(cid, {}).update(params["props"])
            return _FakeResult([])

        # MATCH single Claim by claim_id.
        m = re.match(
            r"MATCH \(c:Claim \{claim_id: \$claim_id\}\) RETURN c$", c,
        )
        if m:
            cid = params["claim_id"]
            node = self.claims.get(cid)
            return _FakeResult([{"c": node}] if node else [])

        # MATCH all Claim nodes.
        if c == "MATCH (c:Claim) RETURN c":
            return _FakeResult([{"c": node} for node in self.claims.values()])

        # MERGE relation between two claims.
        rel_merge = re.match(
            r"MATCH \(s:Claim \{claim_id: \$source_id\}\), "
            r"\(t:Claim \{claim_id: \$target_id\}\) "
            r"MERGE \(s\)-\[r:(\w+)\]->\(t\) "
            r"SET r\.weight = \$weight, r\.created_at = \$created_at$",
            c,
        )
        if rel_merge:
            rel_type = rel_merge.group(1)
            key = (params["source_id"], rel_type, params["target_id"])
            self.relations[key] = {
                "weight": params["weight"],
                "created_at": params["created_at"],
            }
            return _FakeResult([])

        # Relation reads — out / in / both, optionally typed.
        if "RETURN s.claim_id AS s" in c:
            direction = "out" if "{claim_id: $cid})-[" in c else (
                "in" if "->(t:Claim {claim_id: $cid})" in c else "both"
            )
            type_match = re.search(r"\[r:(\w+)\]", c)
            type_filter = type_match.group(1) if type_match else None
            cid = params["cid"]
            rows: list[dict[str, Any]] = []
            for (s, rt, t), props in self.relations.items():
                if type_filter is not None and rt != type_filter:
                    continue
                if direction == "out" and s != cid:
                    continue
                if direction == "in" and t != cid:
                    continue
                if direction == "both" and s != cid and t != cid:
                    continue
                rows.append({
                    "s": s, "t": t, "rt": rt,
                    "w": props["weight"], "c": props["created_at"],
                })
            return _FakeResult(rows)

        # MERGE on a Run node.
        if c.startswith("MERGE (r:Run "):
            rid = params["run_id"]
            self.runs.setdefault(rid, {}).update(params["props"])
            return _FakeResult([])

        # MATCH single Run by run_id.
        if re.match(
            r"MATCH \(r:Run \{run_id: \$run_id\}\) RETURN r$", c,
        ):
            rid = params["run_id"]
            node = self.runs.get(rid)
            return _FakeResult([{"r": node}] if node else [])

        # MERGE OperatorEvent and link to run.
        if "MERGE (e:OperatorEvent" in c and "PRODUCED" in c:
            rid = params["run_id"]
            eid = params["event_id"]
            self.events.setdefault(eid, {}).update(params["props"])
            self.run_produced.setdefault(rid, set()).add(eid)
            return _FakeResult([])

        # Events for run.
        if "MATCH (r:Run" in c and "PRODUCED" in c and "RETURN e" in c:
            rid = params["run_id"]
            ids = self.run_produced.get(rid, set())
            rows = [{"e": self.events[eid]} for eid in ids]
            rows.sort(key=lambda row: row["e"].get("loop_index", 0))
            return _FakeResult(rows)

        raise AssertionError(f"FakeGraph received unexpected Cypher: {c!r}")


class _FakeDriver:
    def __init__(self) -> None:
        self.graph = _FakeGraph()
        self.closed = False

    @contextmanager
    def session(self, database: str = "neo4j"):
        sess = _FakeSession(self.graph)
        try:
            yield sess
        finally:
            return None

    def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fixture_claim(**overrides) -> Claim:
    base = dict(
        content="Water boils at 100C at sea level.",
        method="T6[hypothesis_builder]",
        state=ClaimState.PROPOSED,
        confidence=0.8,
        version=1,
        provenance=Provenance(
            source="des_v0.1",
            run_id="run_xyz",
            operator_path=("T6",),
            timestamp=datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc),
        ),
    )
    base.update(overrides)
    return Claim(**base)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_neo4jstore_requires_driver_or_uri() -> None:
    with pytest.raises(ValueError):
        Neo4jStore(driver=None, uri=None)


def test_neo4jstore_raises_when_driver_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(store_module, "_NEO4J_AVAILABLE", False)
    monkeypatch.setattr(store_module, "GraphDatabase", None)
    with pytest.raises(Neo4jDriverNotInstalled):
        Neo4jStore(uri="bolt://nowhere")


def test_neo4jstore_accepts_injected_driver() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    assert store is not None


# Claims --------------------------------------------------------------------


def test_neo4j_write_then_read_claim() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    c = _fixture_claim()
    store.add_claim(c)
    got = store.get_claim(c.claim_id)
    assert got == c


def test_neo4j_get_missing_claim_returns_none() -> None:
    store = Neo4jStore(driver=_FakeDriver())
    assert store.get_claim("c_missing") is None


def test_neo4j_all_claims_yields_all_added() -> None:
    store = Neo4jStore(driver=_FakeDriver())
    a = _fixture_claim(content="alpha", method="T1")
    b = _fixture_claim(content="beta", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    got = {cl.claim_id: cl for cl in store.all_claims()}
    assert got == {a.claim_id: a, b.claim_id: b}


def test_neo4j_add_claim_is_idempotent() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    c = _fixture_claim()
    store.add_claim(c)
    store.add_claim(c)
    assert len(driver.graph.claims) == 1


# Roundtrip: Claim -> Neo4j -> Claim ---------------------------------------


def test_full_roundtrip_preserves_all_claim_fields() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    original = _fixture_claim(
        state=ClaimState.CONFIRMED,
        confidence=0.95,
        version=3,
    )
    store.add_claim(original)
    rebuilt = store.get_claim(original.claim_id)
    assert rebuilt is not None
    assert rebuilt == original
    # And the field-by-field guarantees that the user-facing report uses:
    assert rebuilt.content == original.content
    assert rebuilt.method == original.method
    assert rebuilt.state is original.state
    assert rebuilt.confidence == pytest.approx(original.confidence)
    assert rebuilt.version == original.version
    assert rebuilt.provenance == original.provenance


# Relations -----------------------------------------------------------------


def test_neo4j_relation_write_and_read() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    a = _fixture_claim(content="a", method="T1")
    b = _fixture_claim(content="b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    rel = Relation(
        source_claim_id=a.claim_id,
        target_claim_id=b.claim_id,
        rel_type=RelationType.SUPPORTS,
        weight=0.9,
        created_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
    )
    store.add_relation(rel)
    got = list(store.relations_for(a.claim_id, direction="out"))
    assert len(got) == 1
    assert got[0].source_claim_id == a.claim_id
    assert got[0].target_claim_id == b.claim_id
    assert got[0].rel_type is RelationType.SUPPORTS
    assert got[0].weight == pytest.approx(0.9)


def test_neo4j_relation_filter_by_type() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    a = _fixture_claim(content="a", method="T1")
    b = _fixture_claim(content="b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    store.add_relation(Relation(
        source_claim_id=a.claim_id, target_claim_id=b.claim_id,
        rel_type=RelationType.SUPPORTS,
    ))
    store.add_relation(Relation(
        source_claim_id=a.claim_id, target_claim_id=b.claim_id,
        rel_type=RelationType.CONTRADICTS,
    ))
    sups = list(store.relations_for(
        a.claim_id, rel_type=RelationType.SUPPORTS, direction="out",
    ))
    assert len(sups) == 1
    assert sups[0].rel_type is RelationType.SUPPORTS


# Run + event ---------------------------------------------------------------


def test_neo4j_run_roundtrip() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    run = Run(run_id="r1", label="probe", metadata={"corpus": "n10_adv"})
    store.add_run(run)
    got = store.get_run("r1")
    assert got == run


def test_neo4j_event_attached_to_run() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    store.add_run(Run(run_id="r1"))
    e0 = OperatorEvent(event_id="e0", run_id="r1",
                       operator_code="T6", loop_index=0,
                       sub_role="hypothesis_builder")
    e1 = OperatorEvent(event_id="e1", run_id="r1",
                       operator_code="T2", loop_index=1)
    store.add_event(e0)
    store.add_event(e1)
    got = list(store.events_for_run("r1"))
    # The fake orders by loop_index ASC.
    assert [e.event_id for e in got] == ["e0", "e1"]
    assert got[0].sub_role == "hypothesis_builder"


# Lifecycle -----------------------------------------------------------------


def test_neo4j_close_calls_driver_close() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    store.close()
    assert driver.closed is True

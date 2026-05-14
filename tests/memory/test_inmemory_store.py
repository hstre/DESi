"""Tests for InMemoryStore — the dependency-free reference implementation."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from desi.memory import (
    Claim,
    ClaimState,
    InMemoryStore,
    OperatorEvent,
    Provenance,
    Relation,
    RelationType,
    Run,
)


def _make_claim(content: str, *, run_id: str = "run_1",
                method: str = "T6") -> Claim:
    return Claim(
        content=content,
        method=method,
        state=ClaimState.PROPOSED,
        confidence=0.7,
        provenance=Provenance(source="des_v0.1", run_id=run_id),
    )


# ----------------------------------------------------------------------------
# Claim write + read
# ----------------------------------------------------------------------------


def test_add_and_get_claim() -> None:
    store = InMemoryStore()
    c = _make_claim("alpha")
    store.add_claim(c)
    got = store.get_claim(c.claim_id)
    assert got == c


def test_get_missing_claim_returns_none() -> None:
    store = InMemoryStore()
    assert store.get_claim("c_does_not_exist") is None


def test_add_same_claim_twice_is_idempotent() -> None:
    store = InMemoryStore()
    c = _make_claim("alpha")
    store.add_claim(c)
    store.add_claim(c)
    assert list(store.all_claims()) == [c]


def test_all_claims_yields_in_insertion_order() -> None:
    store = InMemoryStore()
    a = _make_claim("alpha", method="T1")
    b = _make_claim("beta", method="T2")
    c = _make_claim("gamma", method="T3")
    for claim in (a, b, c):
        store.add_claim(claim)
    assert list(store.all_claims()) == [a, b, c]


# ----------------------------------------------------------------------------
# Relations
# ----------------------------------------------------------------------------


def test_relations_for_out_direction() -> None:
    store = InMemoryStore()
    a = _make_claim("a", method="T1")
    b = _make_claim("b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    rel = Relation(
        source_claim_id=a.claim_id,
        target_claim_id=b.claim_id,
        rel_type=RelationType.SUPPORTS,
    )
    store.add_relation(rel)
    assert list(store.relations_for(a.claim_id, direction="out")) == [rel]
    assert list(store.relations_for(b.claim_id, direction="out")) == []


def test_relations_for_in_direction() -> None:
    store = InMemoryStore()
    a = _make_claim("a", method="T1")
    b = _make_claim("b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    rel = Relation(
        source_claim_id=a.claim_id,
        target_claim_id=b.claim_id,
        rel_type=RelationType.CONTRADICTS,
    )
    store.add_relation(rel)
    assert list(store.relations_for(b.claim_id, direction="in")) == [rel]
    assert list(store.relations_for(a.claim_id, direction="in")) == []


def test_relations_for_both_direction() -> None:
    store = InMemoryStore()
    a = _make_claim("a", method="T1")
    b = _make_claim("b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    r1 = Relation(source_claim_id=a.claim_id, target_claim_id=b.claim_id,
                  rel_type=RelationType.REFINES)
    r2 = Relation(source_claim_id=b.claim_id, target_claim_id=a.claim_id,
                  rel_type=RelationType.DERIVES_FROM)
    store.add_relation(r1)
    store.add_relation(r2)
    both = list(store.relations_for(a.claim_id, direction="both"))
    assert sorted(both, key=lambda r: r.rel_type.value) == sorted(
        [r1, r2], key=lambda r: r.rel_type.value,
    )


def test_relations_for_filters_by_type() -> None:
    store = InMemoryStore()
    a = _make_claim("a", method="T1")
    b = _make_claim("b", method="T2")
    store.add_claim(a)
    store.add_claim(b)
    r_sup = Relation(source_claim_id=a.claim_id, target_claim_id=b.claim_id,
                     rel_type=RelationType.SUPPORTS)
    r_con = Relation(source_claim_id=a.claim_id, target_claim_id=b.claim_id,
                     rel_type=RelationType.CONTRADICTS)
    store.add_relation(r_sup)
    store.add_relation(r_con)
    got = list(store.relations_for(
        a.claim_id, rel_type=RelationType.SUPPORTS, direction="out",
    ))
    assert got == [r_sup]


def test_invalid_direction_raises() -> None:
    store = InMemoryStore()
    with pytest.raises(ValueError):
        list(store.relations_for("c_x", direction="sideways"))


# ----------------------------------------------------------------------------
# Runs and events
# ----------------------------------------------------------------------------


def test_run_roundtrip() -> None:
    store = InMemoryStore()
    run = Run(run_id="r1", label="adversarial-pass-1",
              metadata={"corpus": "n10_adv", "seed": 42})
    store.add_run(run)
    assert store.get_run("r1") == run


def test_event_roundtrip_and_ordering() -> None:
    store = InMemoryStore()
    run = Run(run_id="r1")
    store.add_run(run)
    e0 = OperatorEvent(event_id="e0", run_id="r1",
                       operator_code="T6", loop_index=0,
                       sub_role="hypothesis_builder")
    e1 = OperatorEvent(event_id="e1", run_id="r1",
                       operator_code="T2", loop_index=1)
    store.add_event(e0)
    store.add_event(e1)
    got = list(store.events_for_run("r1"))
    assert sorted(got, key=lambda e: e.event_id) == [e0, e1]


def test_events_for_run_filters_by_run() -> None:
    store = InMemoryStore()
    store.add_run(Run(run_id="r1"))
    store.add_run(Run(run_id="r2"))
    e_r1 = OperatorEvent(event_id="e1", run_id="r1",
                         operator_code="T1", loop_index=0)
    e_r2 = OperatorEvent(event_id="e2", run_id="r2",
                         operator_code="T1", loop_index=0)
    store.add_event(e_r1)
    store.add_event(e_r2)
    assert list(store.events_for_run("r1")) == [e_r1]
    assert list(store.events_for_run("r2")) == [e_r2]


def test_close_is_no_op() -> None:
    store = InMemoryStore()
    # Should not raise.
    store.close()

"""Tests for MemoryRecorder — central writer for runs / events / claims."""
from __future__ import annotations

import pytest

from desi.memory import (
    Claim,
    ClaimState,
    InMemoryStore,
    MemoryRecorder,
    RecorderError,
    RelationType,
)


# ---------------------------------------------------------------------------
# Run lifecycle
# ---------------------------------------------------------------------------


def test_start_run_persists_run_with_model_and_config_hash() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    run = rec.start_run(model="claude-opus-4-7",
                        config={"seed": 7, "temperature": 0.0})
    persisted = store.get_run(run.run_id)
    assert persisted is not None
    assert persisted.run_id == run.run_id
    assert persisted.metadata["model"] == "claude-opus-4-7"
    # config_hash is deterministic and non-empty.
    assert persisted.metadata["config_hash"]
    assert len(persisted.metadata["config_hash"]) == 16


def test_starting_a_second_run_without_ending_raises() -> None:
    rec = MemoryRecorder(InMemoryStore())
    rec.start_run(model="m")
    with pytest.raises(RecorderError):
        rec.start_run(model="m")


def test_end_run_sets_finished_at() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    run = rec.start_run(model="m")
    ended = rec.end_run()
    assert ended.finished_at is not None
    # Persisted version reflects the close timestamp.
    assert store.get_run(run.run_id).finished_at is not None
    assert rec.active_run is None


def test_end_run_without_active_run_raises() -> None:
    rec = MemoryRecorder(InMemoryStore())
    with pytest.raises(RecorderError):
        rec.end_run()


def test_optional_prompt_hash_is_recorded() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    run = rec.start_run(model="m", prompt_hash="ph_deadbeef")
    persisted = store.get_run(run.run_id)
    assert persisted.metadata["prompt_hash"] == "ph_deadbeef"


# ---------------------------------------------------------------------------
# Operator events
# ---------------------------------------------------------------------------


def test_operator_event_persists_under_active_run() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    run = rec.start_run(model="m")
    ev = rec.record_operator_event(
        operator_name="T6",
        input_claims=("c_in",),
        output_claims=("c_out",),
        guard_result="passed",
        sub_role="hypothesis_builder",
    )
    persisted = list(store.events_for_run(run.run_id))
    assert ev in persisted
    assert persisted[0].operator_code == "T6"
    assert persisted[0].sub_role == "hypothesis_builder"
    assert persisted[0].input_claim_ids == ("c_in",)
    assert persisted[0].payload.get("guard_result") == "passed"


def test_operator_event_outside_run_raises() -> None:
    rec = MemoryRecorder(InMemoryStore())
    with pytest.raises(RecorderError):
        rec.record_operator_event(operator_name="T6")


def test_loop_index_auto_increments() -> None:
    rec = MemoryRecorder(InMemoryStore())
    rec.start_run(model="m")
    a = rec.record_operator_event(operator_name="T1")
    b = rec.record_operator_event(operator_name="T2")
    c = rec.record_operator_event(operator_name="T3")
    assert (a.loop_index, b.loop_index, c.loop_index) == (0, 1, 2)


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


def test_record_claim_persists_with_run_provenance() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    run = rec.start_run(model="m")
    c = rec.record_claim(
        content="alpha", method="T6",
        operator_path=("T6",),
    )
    assert store.get_claim(c.claim_id) == c
    assert c.provenance.run_id == run.run_id
    assert c.provenance.operator_path == ("T6",)
    assert c.state is ClaimState.PROPOSED
    assert c.version == 1


def test_record_revision_bumps_version_and_keeps_id() -> None:
    rec = MemoryRecorder(InMemoryStore())
    rec.start_run(model="m")
    c = rec.record_claim(content="alpha", method="T6")
    revised = rec.record_revision(c, new_content="alpha v2",
                                  new_state=ClaimState.CONFIRMED,
                                  new_confidence=0.9)
    assert revised.claim_id == c.claim_id
    assert revised.version == c.version + 1
    assert revised.content == "alpha v2"
    assert revised.state is ClaimState.CONFIRMED
    assert revised.confidence == 0.9


def test_record_claim_outside_run_raises() -> None:
    rec = MemoryRecorder(InMemoryStore())
    with pytest.raises(RecorderError):
        rec.record_claim(content="x", method="T6")


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


def test_record_relation_persists() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="m")
    a = rec.record_claim(content="a", method="T1")
    b = rec.record_claim(content="b", method="T2")
    r = rec.record_relation(source=a, target=b,
                            rel_type=RelationType.SUPPORTS)
    rels = list(store.relations_for(a.claim_id, direction="out"))
    assert r in rels
    assert rels[0].rel_type is RelationType.SUPPORTS


def test_record_relation_accepts_string_ids() -> None:
    store = InMemoryStore()
    rec = MemoryRecorder(store)
    rec.start_run(model="m")
    a = rec.record_claim(content="a", method="T1")
    b = rec.record_claim(content="b", method="T2")
    rec.record_relation(source=a.claim_id, target=b.claim_id,
                        rel_type=RelationType.REFINES)
    rels = list(store.relations_for(a.claim_id, direction="out"))
    assert rels[0].source_claim_id == a.claim_id
    assert rels[0].target_claim_id == b.claim_id


def test_record_relation_outside_run_raises() -> None:
    rec = MemoryRecorder(InMemoryStore())
    with pytest.raises(RecorderError):
        rec.record_relation(source="c_a", target="c_b",
                            rel_type=RelationType.SUPPORTS)


# ---------------------------------------------------------------------------
# Read-only handle
# ---------------------------------------------------------------------------


def test_read_only_view_returns_distinct_object() -> None:
    rec = MemoryRecorder(InMemoryStore())
    view = rec.read_only_view()
    # The view's public surface has no write methods.
    for attr in ("add_claim", "add_relation", "add_run", "add_event",
                 "record_claim", "record_operator_event"):
        assert not hasattr(view, attr), \
            f"view should not expose {attr}; that is recorder territory"

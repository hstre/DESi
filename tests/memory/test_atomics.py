"""Tests for the atomic merge / split helpers on MemoryRecorder."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from desi.memory import (
    Claim,
    ClaimState,
    InMemoryStore,
    MemoryRecorder,
    Provenance,
    RecorderError,
    Relation,
    RelationType,
)


def _seed_recorder() -> MemoryRecorder:
    rec = MemoryRecorder(InMemoryStore())
    rec.start_run(model="m")
    return rec


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def test_merge_succeeds_atomically() -> None:
    rec = _seed_recorder()
    store = rec._store
    a = rec.record_claim(content="alpha", method="T6")
    b = rec.record_claim(content="alpha v2", method="T6")
    target = rec.record_claim(content="alpha consolidated", method="T2")
    result = rec.merge_claims([a, b], target)
    # The target survives.
    assert result.claim_id == target.claim_id
    assert store.get_claim(target.claim_id) is not None
    # Each source is now MERGED with version bumped.
    for src in (a, b):
        stored = store.get_claim(src.claim_id)
        assert stored is not None
        assert stored.state is ClaimState.MERGED
        assert stored.version == src.version + 1
    # Each source has a MERGED_INTO -> target edge.
    for src in (a, b):
        rels = list(store.relations_for(src.claim_id,
                                        rel_type=RelationType.MERGED_INTO,
                                        direction="out"))
        assert len(rels) == 1
        assert rels[0].target_claim_id == target.claim_id


def test_merge_rolls_back_on_failure() -> None:
    rec = _seed_recorder()
    store = rec._store
    a = rec.record_claim(content="alpha", method="T6")
    b = rec.record_claim(content="alpha v2", method="T6")
    target = rec.record_claim(content="alpha consolidated", method="T2")
    pre_claims = list(store.all_claims())
    pre_relations = list(store._relations)
    # Inject a failure in the middle of the merge.
    real_add_relation = store.add_relation
    call_count = {"n": 0}

    def fail_on_second_relation(rel):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated DB error mid-merge")
        return real_add_relation(rel)

    with patch.object(store, "add_relation", side_effect=fail_on_second_relation):
        with pytest.raises(RuntimeError, match="simulated DB error"):
            rec.merge_claims([a, b], target)

    # Roll back: state must look exactly as before the merge.
    assert list(store.all_claims()) == pre_claims
    assert store._relations == pre_relations


def test_merge_rejects_empty_sources() -> None:
    rec = _seed_recorder()
    target = rec.record_claim(content="t", method="T1")
    with pytest.raises(RecorderError):
        rec.merge_claims([], target)


def test_merge_rejects_self_in_sources() -> None:
    rec = _seed_recorder()
    a = rec.record_claim(content="a", method="T1")
    with pytest.raises(RecorderError):
        rec.merge_claims([a], a)


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------


def test_split_succeeds_atomically() -> None:
    rec = _seed_recorder()
    store = rec._store
    source = rec.record_claim(content="parent", method="T1")
    child_a = Claim(
        content="parent-part-A",
        method="T1",
        provenance=Provenance(source="desi", run_id="run_test_split_a"),
    )
    child_b = Claim(
        content="parent-part-B",
        method="T1",
        provenance=Provenance(source="desi", run_id="run_test_split_b"),
    )
    stored_children = rec.split_claim(source, [child_a, child_b])
    # Children persisted.
    for ch in stored_children:
        assert store.get_claim(ch.claim_id) is not None
    # Source upgraded to SPLIT.
    re_source = store.get_claim(source.claim_id)
    assert re_source.state is ClaimState.SPLIT
    assert re_source.version == source.version + 1
    # Each child has SPLIT_FROM -> source.
    for ch in stored_children:
        rels = list(store.relations_for(ch.claim_id,
                                        rel_type=RelationType.SPLIT_FROM,
                                        direction="out"))
        assert len(rels) == 1
        assert rels[0].target_claim_id == source.claim_id


def test_split_rolls_back_on_failure() -> None:
    rec = _seed_recorder()
    store = rec._store
    source = rec.record_claim(content="parent", method="T1")
    child_a = Claim(
        content="A",
        method="T1",
        provenance=Provenance(source="desi", run_id="run_test_split_a2"),
    )
    child_b = Claim(
        content="B",
        method="T1",
        provenance=Provenance(source="desi", run_id="run_test_split_b2"),
    )
    pre_claims = list(store.all_claims())
    pre_relations = list(store._relations)
    real_add_claim = store.add_claim
    call_count = {"n": 0}

    def fail_on_second_child(claim):
        # Order inside split_claim: add child_a, edge_a, add child_b, edge_b,
        # add updated source. We fail when we see child_b coming in.
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated DB error during split")
        return real_add_claim(claim)

    with patch.object(store, "add_claim", side_effect=fail_on_second_child):
        with pytest.raises(RuntimeError, match="simulated DB error"):
            rec.split_claim(source, [child_a, child_b])

    assert list(store.all_claims()) == pre_claims
    assert store._relations == pre_relations


def test_split_rejects_empty_children() -> None:
    rec = _seed_recorder()
    source = rec.record_claim(content="parent", method="T1")
    with pytest.raises(RecorderError):
        rec.split_claim(source, [])


def test_split_rejects_self_in_children() -> None:
    rec = _seed_recorder()
    source = rec.record_claim(content="parent", method="T1")
    with pytest.raises(RecorderError):
        rec.split_claim(source, [source])


# ---------------------------------------------------------------------------
# Transaction nesting / no-op outer
# ---------------------------------------------------------------------------


def test_inmemory_transaction_commits_on_success() -> None:
    store = InMemoryStore()
    with store.transaction():
        # Manually add a claim through the store API; on success it
        # should remain visible after the block.
        c = Claim(content="x", method="m",
                  provenance=Provenance(source="s", run_id="r"))
        store.add_claim(c)
    assert store.get_claim(c.claim_id) is not None


def test_inmemory_transaction_rolls_back_on_exception() -> None:
    store = InMemoryStore()
    pre = list(store.all_claims())
    with pytest.raises(RuntimeError):
        with store.transaction():
            c = Claim(content="x", method="m",
                      provenance=Provenance(source="s", run_id="r"))
            store.add_claim(c)
            raise RuntimeError("nope")
    assert list(store.all_claims()) == pre

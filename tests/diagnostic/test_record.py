"""Tests for v2.1 DeficitRecord (Aufgabe 3)."""
from __future__ import annotations

import pytest

from desi.diagnostic import DeficitCategory, DeficitRecord


def _build(**overrides):
    base = dict(
        category=DeficitCategory.DEAD_MUTATION_KNOB,
        source_module="desi.sandbox",
        source_case_ids=("step_1", "step_2"),
        frequency=2,
        severity_score=0.5,
        confidence_score=0.5,
        is_actionable=True,
        candidate_knobs=("branch_open_evidence_min",),
        rationale="test record",
    )
    base.update(overrides)
    return DeficitRecord.build(**base)


def test_required_fields_present() -> None:
    rec = _build()
    for f in (
        "deficit_id", "category", "source_module", "source_case_ids",
        "frequency", "severity_score", "confidence_score",
        "is_actionable", "candidate_knobs", "rationale", "replay_hash",
    ):
        assert hasattr(rec, f), f


def test_replay_hash_is_deterministic_for_same_inputs() -> None:
    a = _build()
    b = _build()
    assert a.replay_hash == b.replay_hash
    assert a.deficit_id == b.deficit_id


def test_replay_hash_invariant_under_case_id_reordering() -> None:
    a = _build(source_case_ids=("step_1", "step_2"))
    b = _build(source_case_ids=("step_2", "step_1"))
    assert a.replay_hash == b.replay_hash


def test_replay_hash_changes_when_severity_changes() -> None:
    a = _build(severity_score=0.5)
    b = _build(severity_score=0.7)
    assert a.replay_hash != b.replay_hash


def test_unknown_knob_rejected_by_knob_invariant() -> None:
    with pytest.raises(ValueError):
        _build(candidate_knobs=("not_a_real_knob",))


def test_known_knob_accepted() -> None:
    rec = _build(candidate_knobs=("RecursiveResolver.max_depth",))
    assert rec.candidate_knobs == ("RecursiveResolver.max_depth",)


def test_severity_out_of_range_rejected() -> None:
    with pytest.raises(ValueError):
        DeficitRecord(
            deficit_id="df_x", category=DeficitCategory.UNKNOWN,
            source_module="x", source_case_ids=(), frequency=0,
            severity_score=1.5, confidence_score=0.5,
            is_actionable=False, candidate_knobs=(),
            rationale="bad", replay_hash="0" * 16,
        )


def test_confidence_out_of_range_rejected() -> None:
    with pytest.raises(ValueError):
        DeficitRecord(
            deficit_id="df_x", category=DeficitCategory.UNKNOWN,
            source_module="x", source_case_ids=(), frequency=0,
            severity_score=0.5, confidence_score=-0.1,
            is_actionable=False, candidate_knobs=(),
            rationale="bad", replay_hash="0" * 16,
        )


def test_to_dict_round_trip_shape() -> None:
    rec = _build()
    d = rec.to_dict()
    for k in (
        "deficit_id", "category", "source_module", "source_case_ids",
        "frequency", "severity_score", "confidence_score",
        "is_actionable", "candidate_knobs", "rationale",
        "self_reference", "replay_hash",
    ):
        assert k in d

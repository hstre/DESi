"""Tests for v2.6 hypothetical trigger + helpers (Aufgaben 2, 4)."""
from __future__ import annotations

from desi.causal_probe import (
    BenchmarkSource,
    candidate_replay_hash,
    count_atomic_sequence,
    count_repeated_content,
    hypothetical_trigger,
)


# ---------------------------------------------------------------------------
# hypothetical_trigger
# ---------------------------------------------------------------------------


def test_trigger_silent_when_no_therefore() -> None:
    fired, reason = hypothetical_trigger(
        premise_count=3, therefore_count=0, atomic_sequence=3,
    )
    assert fired is False
    assert "therefore_count" in reason


def test_trigger_silent_when_no_premises() -> None:
    fired, reason = hypothetical_trigger(
        premise_count=0, therefore_count=1, atomic_sequence=2,
    )
    assert fired is False
    assert "premise_count" in reason


def test_trigger_silent_when_atomic_sequence_too_short() -> None:
    fired, reason = hypothetical_trigger(
        premise_count=3, therefore_count=1, atomic_sequence=1,
    )
    assert fired is False
    assert "atomic_sequence" in reason


def test_trigger_fires_on_directive_canonical_shape() -> None:
    fired, reason = hypothetical_trigger(
        premise_count=3, therefore_count=1, atomic_sequence=3,
    )
    assert fired is True
    assert "atomic_sequence=3" in reason


def test_trigger_is_deterministic() -> None:
    args = dict(premise_count=2, therefore_count=2, atomic_sequence=2)
    a = hypothetical_trigger(**args)
    b = hypothetical_trigger(**args)
    assert a == b


# ---------------------------------------------------------------------------
# count_atomic_sequence
# ---------------------------------------------------------------------------


def test_atomic_sequence_zero_for_empty() -> None:
    assert count_atomic_sequence(()) == 0


def test_atomic_sequence_counts_longest_run() -> None:
    assert count_atomic_sequence(("atomic", "atomic", "atomic")) == 3


def test_atomic_sequence_breaks_on_non_atomic() -> None:
    assert count_atomic_sequence((
        "atomic", "atomic", "universal", "atomic",
    )) == 2


def test_atomic_sequence_treats_particular_as_atomic() -> None:
    assert count_atomic_sequence(("particular", "atomic")) == 2


# ---------------------------------------------------------------------------
# count_repeated_content
# ---------------------------------------------------------------------------


def test_repeated_content_zero_when_no_overlap() -> None:
    subj, pred = count_repeated_content("The cat sleeps. The sun rises.")
    assert subj == 0
    assert pred == 0


def test_repeated_content_detects_shared_token() -> None:
    subj, pred = count_repeated_content(
        "The rain falls. The rain wets the street.",
    )
    assert subj >= 1


def test_repeated_content_is_deterministic() -> None:
    a = count_repeated_content(
        "A storm arrived. Trees fell. Power lines snapped.",
    )
    b = count_repeated_content(
        "A storm arrived. Trees fell. Power lines snapped.",
    )
    assert a == b


# ---------------------------------------------------------------------------
# BenchmarkSource enum
# ---------------------------------------------------------------------------


def test_benchmark_source_has_two_values() -> None:
    assert len(list(BenchmarkSource)) == 2


def test_benchmark_source_values() -> None:
    assert BenchmarkSource.MAIN_50.value == "main_50"
    assert BenchmarkSource.MULTISTEP_30.value == "multistep_30"


# ---------------------------------------------------------------------------
# replay hash
# ---------------------------------------------------------------------------


def test_replay_hash_is_sixteen_hex() -> None:
    h = candidate_replay_hash({"case_id": "X", "premise_count": 2})
    assert len(h) == 16
    int(h, 16)


def test_replay_hash_ignores_its_own_field() -> None:
    a = candidate_replay_hash({"case_id": "X", "replay_hash": "a"})
    b = candidate_replay_hash({"case_id": "X", "replay_hash": "b"})
    assert a == b


def test_replay_hash_changes_on_payload_change() -> None:
    a = candidate_replay_hash({"case_id": "X", "premise_count": 1})
    b = candidate_replay_hash({"case_id": "X", "premise_count": 2})
    assert a != b

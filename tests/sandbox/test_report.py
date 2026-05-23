"""Tests for the v2.0 EvolutionReport summary detectors (Aufgabe 6)."""
from __future__ import annotations

from desi.sandbox import (
    compute_replay_hash,
    detect_convergence,
    detect_drift,
    detect_local_optimum,
    detect_oscillation,
)


# ---------------------------------------------------------------------------
# detect_oscillation
# ---------------------------------------------------------------------------


def test_oscillation_detected_in_zigzag() -> None:
    values = [0.45, 0.47, 0.45, 0.47, 0.45]
    assert detect_oscillation(values) is True


def test_oscillation_not_detected_in_monotonic() -> None:
    values = [0.30, 0.32, 0.34, 0.36, 0.38]
    assert detect_oscillation(values) is False


def test_oscillation_not_detected_in_short_series() -> None:
    assert detect_oscillation([0.45, 0.47, 0.45]) is False
    assert detect_oscillation([0.45]) is False
    assert detect_oscillation([]) is False


# ---------------------------------------------------------------------------
# detect_convergence
# ---------------------------------------------------------------------------


def test_convergence_detected_in_flat_tail() -> None:
    values = [0.30, 0.35, 0.40, 0.40, 0.40, 0.40, 0.40]
    assert detect_convergence(values, window=5) is True


def test_convergence_not_detected_when_tail_moves() -> None:
    values = [0.30, 0.35, 0.40, 0.42, 0.44, 0.46]
    assert detect_convergence(values, window=5) is False


def test_convergence_returns_false_for_short_series() -> None:
    assert detect_convergence([0.45], window=5) is False


# ---------------------------------------------------------------------------
# detect_local_optimum
# ---------------------------------------------------------------------------


def test_local_optimum_detected_when_peak_in_middle() -> None:
    values = [0.40, 0.45, 0.50, 0.48, 0.46]
    assert detect_local_optimum(values) is True


def test_local_optimum_not_detected_when_still_climbing() -> None:
    values = [0.40, 0.42, 0.44, 0.46]
    assert detect_local_optimum(values) is False


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------


def test_drift_detected_when_cumulative_change_exceeds_threshold() -> None:
    values = [0.30, 0.34, 0.38, 0.42, 0.46]
    assert detect_drift(values, threshold=0.10) is True


def test_drift_not_detected_when_change_below_threshold() -> None:
    values = [0.45, 0.46, 0.47, 0.46, 0.45]
    assert detect_drift(values, threshold=0.10) is False


# ---------------------------------------------------------------------------
# compute_replay_hash
# ---------------------------------------------------------------------------


def test_replay_hash_is_sixteen_hex_chars() -> None:
    h = compute_replay_hash({"a": 1, "b": [2, 3]})
    assert len(h) == 16
    int(h, 16)   # raises if non-hex


def test_replay_hash_independent_of_timestamp() -> None:
    a = compute_replay_hash({
        "a": 1, "started_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T00:01:00",
    })
    b = compute_replay_hash({
        "a": 1, "started_at": "2030-12-31T00:00:00",
        "finished_at": "2030-12-31T00:01:00",
    })
    assert a == b


def test_replay_hash_independent_of_key_order() -> None:
    a = compute_replay_hash({"a": 1, "b": 2, "c": 3})
    b = compute_replay_hash({"c": 3, "b": 2, "a": 1})
    assert a == b


def test_replay_hash_changes_when_payload_changes() -> None:
    a = compute_replay_hash({"a": 1})
    b = compute_replay_hash({"a": 2})
    assert a != b


def test_replay_hash_ignores_its_own_field() -> None:
    a = compute_replay_hash({"a": 1, "replay_hash": "abc"})
    b = compute_replay_hash({"a": 1, "replay_hash": "def"})
    assert a == b

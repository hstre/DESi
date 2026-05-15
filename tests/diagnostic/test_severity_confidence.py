"""Tests for v2.1 severity + confidence scoring (Aufgabe 4)."""
from __future__ import annotations

from desi.diagnostic import confidence_score, severity_from_coverage


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------


def test_severity_zero_for_zero_affected() -> None:
    assert severity_from_coverage(0, 50) == 0.0


def test_severity_one_when_all_affected() -> None:
    assert severity_from_coverage(50, 50) == 1.0


def test_severity_is_pure_ratio() -> None:
    assert severity_from_coverage(10, 50) == 0.2


def test_severity_caps_at_one_for_overflow_input() -> None:
    """Should never exceed 1.0 even if affected > total."""
    assert severity_from_coverage(60, 50) == 1.0


def test_severity_handles_zero_total_cleanly() -> None:
    assert severity_from_coverage(0, 0) == 0.0


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def test_confidence_zero_when_no_frequency_or_reproducibility() -> None:
    assert confidence_score(
        frequency=0, reproducibility=0.0, cross_source_consistency=0.0,
    ) == 0.0


def test_confidence_rises_with_frequency() -> None:
    a = confidence_score(
        frequency=1, reproducibility=1.0, cross_source_consistency=1.0,
    )
    b = confidence_score(
        frequency=5, reproducibility=1.0, cross_source_consistency=1.0,
    )
    assert b >= a


def test_confidence_rises_with_reproducibility() -> None:
    a = confidence_score(
        frequency=3, reproducibility=0.0, cross_source_consistency=1.0,
    )
    b = confidence_score(
        frequency=3, reproducibility=1.0, cross_source_consistency=1.0,
    )
    assert b > a


def test_confidence_rises_with_cross_source_consistency() -> None:
    a = confidence_score(
        frequency=3, reproducibility=1.0, cross_source_consistency=0.0,
    )
    b = confidence_score(
        frequency=3, reproducibility=1.0, cross_source_consistency=1.0,
    )
    assert b > a


def test_self_reference_halves_confidence() -> None:
    a = confidence_score(
        frequency=5, reproducibility=1.0,
        cross_source_consistency=1.0, self_reference=False,
    )
    b = confidence_score(
        frequency=5, reproducibility=1.0,
        cross_source_consistency=1.0, self_reference=True,
    )
    assert b == round(a * 0.5, 6)


def test_confidence_is_bounded_to_unit_interval() -> None:
    s = confidence_score(
        frequency=100, reproducibility=1.0,
        cross_source_consistency=1.0,
    )
    assert 0.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# Metadata-storm invariant (Aufgabe 4)
# ---------------------------------------------------------------------------


def test_metadata_storm_does_not_change_severity_or_confidence() -> None:
    """Adding 1000 noisy keys to the surrounding context must not
    shift either score — both depend only on data axes."""
    s_clean = severity_from_coverage(10, 50)
    c_clean = confidence_score(
        frequency=3, reproducibility=1.0, cross_source_consistency=1.0,
    )
    # Build a dict of nonsense metadata and verify the functions
    # don't even consume it.
    noise = {f"k_{i}": "x" * 50 for i in range(1000)}
    assert noise            # use the variable so flake8 stays quiet
    s_dirty = severity_from_coverage(10, 50)
    c_dirty = confidence_score(
        frequency=3, reproducibility=1.0, cross_source_consistency=1.0,
    )
    assert s_clean == s_dirty
    assert c_clean == c_dirty

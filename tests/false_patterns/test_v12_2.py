"""v12.2 - false pattern resistance tests."""
from __future__ import annotations

import json
import pathlib

from desi.false_patterns.collapse import (
    collapse_event_count, epistemic_collapse,
)
from desi.false_patterns.epistemic_pressure import (
    epistemic_integrity, speculative_drift,
)
from desi.false_patterns.pattern_detection import (
    FALSE_PATTERN_KINDS, FalsePatternKind,
    classified_patterns, detect_kind, fixture,
    kind_counts,
)
from desi.false_patterns.report import (
    build_false_patterns_artifact, build_report,
)
from desi.false_patterns.spurious_correlations import (
    false_certainty_rate,
    false_pattern_detection,
    genuine_kept_rate,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "open_math"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_false_pattern_kinds_closed_set() -> None:
    assert FALSE_PATTERN_KINDS == tuple(
        k.value for k in FalsePatternKind
    )
    assert len(FALSE_PATTERN_KINDS) == 5


def test_fixture_balanced() -> None:
    counts = kind_counts()
    assert set(counts.keys()) == set(
        FALSE_PATTERN_KINDS,
    )
    assert set(counts.values()) == {2}


def test_false_pattern_detection_full() -> None:
    """Pflichtfrage 2: wie viele werden
    erkannt?"""
    assert false_pattern_detection() >= 0.90


def test_false_certainty_rate_zero() -> None:
    """Pflichtfrage 3: wie hoch bleibt false
    certainty?"""
    assert false_certainty_rate() <= 0.05


def test_speculative_drift_low() -> None:
    """Pflichtfrage 4: wie stark waechst
    speculative drift? Speculative drift =
    falsche Klassifikation in die andere
    Richtung (genuine flagged as false). Should
    be very low."""
    assert speculative_drift() <= 0.10


def test_epistemic_integrity_high() -> None:
    """Pflichtfrage 5: bleibt epistemische
    Integritaet erhalten?"""
    assert epistemic_integrity() >= 0.90


def test_genuine_kept_rate_full() -> None:
    """Every genuine pattern stays GENUINE."""
    assert genuine_kept_rate() == 1.0


def test_no_epistemic_collapse() -> None:
    """Directive's gate: epistemic_collapse
    must equal 0."""
    assert epistemic_collapse() == 0
    assert collapse_event_count() == 0


def test_detect_numerology() -> None:
    assert detect_kind(
        "Every 17th prime carries a special "
        "structural meaning.",
    ) == FalsePatternKind.NUMEROLOGICAL


def test_detect_small_sample() -> None:
    assert detect_kind(
        "We tested 5 even numbers and the "
        "pattern holds.",
    ) == FalsePatternKind.SMALL_SAMPLE


def test_detect_genuine() -> None:
    assert detect_kind(
        "The set of primes is infinite "
        "(Euclid, proven).",
    ) == FalsePatternKind.GENUINE


def test_classified_patterns_match_fixture() -> (
    None
):
    assert len(classified_patterns()) == len(
        fixture(),
    )


def test_every_classification_correct() -> None:
    """Every detector verdict matches the
    ground-truth kind exactly."""
    for r in classified_patterns():
        assert r.correct, r.to_dict()


def test_replay_stability_one() -> None:
    """Pflichtfrage 1: wie viele falsche
    Muster entstehen? Replay stability anchors
    the deterministic detection."""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PATTERN_RESILIENT",
        "PATTERN_COLLAPSE",
        "PATTERN_FALSE_CERTAINTY",
        "PATTERN_DETECTION_WEAK",
        "PATTERN_SPECULATIVE_DRIFT",
        "PATTERN_INTEGRITY_LOW",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_resilient() -> None:
    """Killerfrage: erkennt DESi mathematische
    Halluzination - oder nur sprachliche?"""
    assert build_report().recommendation == (
        "PATTERN_RESILIENT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v12_2_false_patterns.json")
    assert art["schema_version"] == (
        "v12_2_false_pattern_resistance"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v12_2_false_patterns.json")
    required = {
        "false_pattern_detection",
        "false_certainty_rate",
        "speculative_drift",
        "epistemic_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v12_2_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v12_2_false_patterns.json")
    live = build_false_patterns_artifact()
    assert art == live

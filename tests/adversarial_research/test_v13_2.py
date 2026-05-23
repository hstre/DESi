"""v13.2 - adversarial research tests."""
from __future__ import annotations

import json
import pathlib

from desi.adversarial_research.confidence_inflation import (
    detection_recall_on_inflated,
    false_certainty_rate,
    methodological_integrity,
)
from desi.adversarial_research.manipulation import (
    MANIPULATION_KINDS, ManipulationKind,
    fixture, kind_counts,
)
from desi.adversarial_research.overclaiming import (
    overclaim_detection,
)
from desi.adversarial_research.report import (
    build_adversarial_artifact, build_report,
)
from desi.adversarial_research.selective_reporting import (
    classified_manipulations,
    manipulation_detection,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "paper_integrity"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_manipulation_kinds_closed_set() -> None:
    assert MANIPULATION_KINDS == tuple(
        k.value for k in ManipulationKind
    )
    assert len(MANIPULATION_KINDS) == 7


def test_fixture_covers_all_kinds() -> None:
    """Every closed manipulation kind appears
    in the fixture."""
    seen = {c.kind for c in fixture()}
    assert seen == set(MANIPULATION_KINDS)


def test_manipulation_detection_full() -> None:
    """Pflichtfrage 1: wie viele Manipulationen
    erkennt DESi?"""
    assert manipulation_detection() >= 0.90


def test_every_manipulation_detected() -> None:
    """Stronger: every non-HONEST claim is
    detected as exactly its ground-truth
    kind."""
    for r in classified_manipulations():
        if r.ground_truth_kind != (
            ManipulationKind.HONEST.value
        ):
            assert r.correct


def test_honest_claims_classified_honest() -> (
    None
):
    """Sanity: HONEST claims stay HONEST."""
    for r in classified_manipulations():
        if r.ground_truth_kind == (
            ManipulationKind.HONEST.value
        ):
            assert r.detected_kind == (
                ManipulationKind.HONEST.value
            )


def test_overclaim_detection_full() -> None:
    """Pflichtfrage 3: wie stark waechst
    overclaiming? Every claim with confidence
    gap > 0.20 is detected as non-HONEST."""
    assert overclaim_detection() >= 0.90


def test_detection_on_inflated_full() -> None:
    """Pflichtfrage 4: werden methodologische
    Attrappen erkannt? Every confidence-inflated
    claim (claim >= 0.80, warranted < 0.50) is
    flagged."""
    assert detection_recall_on_inflated() >= (
        0.90
    )


def test_methodological_integrity_reflects_fixture() -> (
    None
):
    """2 of 8 fixture claims are HONEST = 0.25;
    the rest are deliberate manipulations.
    The metric is honest about the corpus
    composition."""
    mi = methodological_integrity()
    assert 0.20 <= mi <= 0.30


def test_false_certainty_rate_reflects_fixture() -> (
    None
):
    """6 of 8 claims have inflated confidence;
    the fraction reflects the deliberately
    adversarial corpus."""
    fcr = false_certainty_rate()
    assert 0.50 <= fcr <= 0.90


def test_replay_stability_one() -> None:
    """Pflichtfrage 5: bleibt epistemische
    Integritaet erhalten? Replay anchors the
    deterministic audit."""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MANIPULATION_RESILIENT",
        "MANIPULATION_LEAK",
        "MANIPULATION_OVERCLAIM_LEAK",
        "MANIPULATION_INFLATION_LEAK",
        "MANIPULATION_HONEST_SHRUNK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_resilient() -> None:
    """Killerfrage: erkennt DESi
    wissenschaftliche Manipulation - auch wenn
    sie sprachlich perfekt aussieht?"""
    assert build_report().recommendation == (
        "MANIPULATION_RESILIENT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v13_2_adversarial.json")
    assert art["schema_version"] == (
        "v13_2_adversarial_research"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v13_2_adversarial.json")
    required = {
        "manipulation_detection",
        "false_certainty_rate",
        "overclaim_detection",
        "methodological_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v13_2_report.json")
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
    art = _load("v13_2_adversarial.json")
    live = build_adversarial_artifact()
    assert art == live

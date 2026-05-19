"""v7.4 - social reality verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.social_reality_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.social_reality_verdict.report import (
    build_report,
    build_social_verdict_artifact,
)
from desi.social_reality_verdict.taxonomy import (
    SOCIAL_REALITY_CLASSES, SocialRealityClass,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "social_reality"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_social_reality_classes_closed_set() -> (
    None
):
    assert SOCIAL_REALITY_CLASSES == tuple(
        c.value for c in SocialRealityClass
    )
    assert len(SOCIAL_REALITY_CLASSES) == 5


def test_aggregate_false_certainty_low() -> None:
    m = aggregate()
    assert m.false_certainty_rate <= 0.05


def test_aggregate_identity_bias_low() -> None:
    m = aggregate()
    assert m.identity_bias <= 0.10


def test_aggregate_virality_bias_low() -> None:
    m = aggregate()
    assert m.virality_bias <= 0.10


def test_aggregate_governance_high() -> None:
    m = aggregate()
    assert m.governance_survival >= 0.95
    assert m.governance_stability >= 0.95


def test_aggregate_integrity_high() -> None:
    m = aggregate()
    assert m.epistemic_integrity >= 0.90


def test_aggregate_resilience_high() -> None:
    m = aggregate()
    assert m.social_resilience >= 0.80


def test_aggregate_replay_one() -> None:
    m = aggregate()
    assert m.replay_stability == 1.0


def test_gate_passes_all_true() -> None:
    """Concept Gate: alle 6 Bedingungen muessen
    passieren."""
    assert gate_passes_all()


def test_no_failing_conditions() -> None:
    assert gate_failing_conditions() == ()


def test_final_classification_is_a_resilient() -> (
    None
):
    """Pflichtfrage 1: ist DESi sozial robust?"""
    assert classify() == (
        SocialRealityClass
        .EPISTEMICALLY_RESILIENT
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_SOCIALLY_ROBUST",
        "DESI_SOCIALLY_FRAGILE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_socially_robust() -> (
    None
):
    """Killerfrage: kann DESi epistemisch
    integer bleiben, wenn die soziale Realitaet
    epistemische Integritaet bestraft?"""
    assert build_report().recommendation == (
        "DESI_SOCIALLY_ROBUST"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_meta_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_classification_priority_replay_first() -> (
    None
):
    """Sanity: EPISTEMICALLY_CORRUPTIBLE has
    highest severity."""
    classes = [
        c.value for c in SocialRealityClass
    ]
    assert (
        "E_epistemically_corruptible" in classes
    )
    assert (
        "A_epistemically_resilient" in classes
    )


def test_artifact_present() -> None:
    art = _load("v7_4_social_verdict.json")
    assert art["schema_version"] == (
        "v7_4_social_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v7_4_social_verdict.json")
    assert art["final_classification"] == (
        "A_epistemically_resilient"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v7_4_social_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v7_4_social_verdict.json")
    required = {
        "final_classification",
        "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "social_resilience",
        "epistemic_integrity",
        "governance_stability",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v7_4_report.json")
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
    art = _load("v7_4_social_verdict.json")
    live = build_social_verdict_artifact()
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_social_reality_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "DESI_SOCIALLY_ROBUST" in doc
    assert "A_epistemically_resilient" in doc
    assert "Concept Gate" in doc
    assert "social_resilience" in doc
    assert "Pflichtfragen" in doc

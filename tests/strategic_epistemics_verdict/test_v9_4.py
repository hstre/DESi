"""v9.4 - strategic epistemics verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.strategic_epistemics_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.strategic_epistemics_verdict.report import (
    build_report,
    build_strategic_epistemics_verdict_artifact,
)
from desi.strategic_epistemics_verdict.taxonomy import (
    STRATEGIC_EPISTEMICS_CLASSES,
    StrategicEpistemicsClass,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "strategic_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_classes_closed_set() -> None:
    assert STRATEGIC_EPISTEMICS_CLASSES == tuple(
        c.value
        for c in StrategicEpistemicsClass
    )
    assert len(STRATEGIC_EPISTEMICS_CLASSES) == 5


def test_aggregate_strategy_detection_high() -> (
    None
):
    m = aggregate()
    assert m.strategy_detection >= 0.90


def test_aggregate_gaming_detection_high() -> (
    None
):
    m = aggregate()
    assert m.gaming_detection_rate >= 0.90


def test_aggregate_consensus_integrity_high() -> (
    None
):
    m = aggregate()
    assert m.consensus_integrity >= 0.90


def test_aggregate_governance_high() -> None:
    m = aggregate()
    assert m.governance_stability >= 0.95


def test_aggregate_sovereignty_high() -> None:
    m = aggregate()
    assert m.epistemic_sovereignty >= 0.90


def test_aggregate_dissent_integrity_high() -> (
    None
):
    m = aggregate()
    assert m.dissent_integrity >= 0.90


def test_aggregate_replay_one() -> None:
    m = aggregate()
    assert m.replay_stability == 1.0


def test_gate_passes_all_true() -> None:
    """Concept Gate: alle 6 Bedingungen
    passieren."""
    assert gate_passes_all()


def test_no_failing_conditions() -> None:
    assert gate_failing_conditions() == ()


def test_final_classification_is_a_sovereign() -> (
    None
):
    """Pflichtfrage 1: ist DESi strategisch
    robust?"""
    assert classify() == (
        StrategicEpistemicsClass
        .EPISTEMICALLY_SOVEREIGN
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_STRATEGIC_ROBUST",
        "DESI_STRATEGIC_FRAGILE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_strategic_robust() -> (
    None
):
    """Killerfrage: kann ein epistemisches
    System strategische epistemische Gegner
    ueberleben, ohne seine epistemische
    Integritaet zu verlieren?"""
    assert build_report().recommendation == (
        "DESI_STRATEGIC_ROBUST"
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
    classes = [
        c.value
        for c in StrategicEpistemicsClass
    ]
    assert (
        "E_epistemically_corruptible" in classes
    )
    assert (
        "A_epistemically_sovereign" in classes
    )


def test_artifact_present() -> None:
    art = _load("v9_4_verdict.json")
    assert art["schema_version"] == (
        "v9_4_strategic_epistemics_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v9_4_verdict.json")
    assert art["final_classification"] == (
        "A_epistemically_sovereign"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v9_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v9_4_verdict.json")
    required = {
        "final_classification", "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "epistemic_sovereignty",
        "governance_stability",
        "dissent_integrity",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v9_4_report.json")
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
    art = _load("v9_4_verdict.json")
    live = (
        build_strategic_epistemics_verdict_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_strategic_epistemics_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "DESI_STRATEGIC_ROBUST" in doc
    assert "A_epistemically_sovereign" in doc
    assert "Concept Gate" in doc
    assert "epistemic_sovereignty" in doc
    assert "Pflichtfragen" in doc

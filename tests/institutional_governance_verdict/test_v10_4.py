"""v10.4 - institutional governance verdict
tests."""
from __future__ import annotations

import json
import pathlib

from desi.institutional_governance_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.institutional_governance_verdict.report import (
    build_institutional_governance_verdict_artifact,
    build_report,
)
from desi.institutional_governance_verdict.taxonomy import (
    INSTITUTIONAL_GOVERNANCE_CLASSES,
    InstitutionalGovernanceClass,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "institutional_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_classes_closed_set() -> None:
    assert (
        INSTITUTIONAL_GOVERNANCE_CLASSES
        == tuple(
            c.value
            for c in InstitutionalGovernanceClass
        )
    )
    assert len(
        INSTITUTIONAL_GOVERNANCE_CLASSES,
    ) == 5


def test_aggregate_power_concentration_low() -> (
    None
):
    m = aggregate()
    assert m.power_concentration <= 0.10


def test_aggregate_authority_drift_low() -> None:
    m = aggregate()
    assert m.authority_drift <= 0.10


def test_aggregate_bad_precedent_low() -> None:
    m = aggregate()
    assert (
        m.bad_precedent_persistence <= 0.10
    )


def test_aggregate_transparency_high() -> None:
    m = aggregate()
    assert m.governance_transparency >= 0.95


def test_aggregate_flexibility_high() -> None:
    m = aggregate()
    assert m.epistemic_flexibility >= 0.90


def test_aggregate_resilience_high() -> None:
    m = aggregate()
    assert m.institutional_resilience >= 0.80


def test_aggregate_replay_one() -> None:
    m = aggregate()
    assert m.replay_stability == 1.0


def test_gate_passes_all_true() -> None:
    """Concept Gate: alle 6 Bedingungen
    passieren."""
    assert gate_passes_all()


def test_no_failing_conditions() -> None:
    assert gate_failing_conditions() == ()


def test_final_classification_is_a() -> None:
    """Pflichtfrage 1: ist DESi institutionell
    robust?"""
    assert classify() == (
        InstitutionalGovernanceClass
        .EPISTEMICALLY_CONSTITUTIONAL
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_INSTITUTIONALLY_ROBUST",
        "DESI_INSTITUTIONALLY_FRAGILE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_institutionally_robust() -> (
    None
):
    """Killerfrage: kann ein epistemisches
    System langfristige Institutionalisierung
    ueberleben, ohne epistemisch buerokratisch
    oder korrupt zu werden?"""
    assert build_report().recommendation == (
        "DESI_INSTITUTIONALLY_ROBUST"
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
        for c in InstitutionalGovernanceClass
    ]
    assert (
        "E_institutionally_corruptible"
        in classes
    )
    assert (
        "A_epistemically_constitutional"
        in classes
    )


def test_artifact_present() -> None:
    art = _load("v10_4_verdict.json")
    assert art["schema_version"] == (
        "v10_4_institutional_"
        "governance_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v10_4_verdict.json")
    assert art["final_classification"] == (
        "A_epistemically_constitutional"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v10_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v10_4_verdict.json")
    required = {
        "final_classification", "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "institutional_resilience",
        "governance_transparency",
        "epistemic_flexibility",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v10_4_report.json")
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
    art = _load("v10_4_verdict.json")
    live = (
        build_institutional_governance_verdict_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_institutional_governance_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "DESI_INSTITUTIONALLY_ROBUST" in doc
    assert (
        "A_epistemically_constitutional" in doc
    )
    assert "Concept Gate" in doc
    assert "institutional_resilience" in doc
    assert "Pflichtfragen" in doc

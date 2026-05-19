"""v11.4 - chess governance verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.chess_governance_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.chess_governance_verdict.report import (
    build_chess_governance_verdict_artifact,
    build_report,
)
from desi.chess_governance_verdict.taxonomy import (
    CHESS_GOVERNANCE_CLASSES,
    ChessGovernanceClass,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "chess_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_classes_closed_set() -> None:
    assert CHESS_GOVERNANCE_CLASSES == tuple(
        c.value for c in ChessGovernanceClass
    )
    assert len(CHESS_GOVERNANCE_CLASSES) == 5


def test_aggregate_compute_reduction() -> None:
    m = aggregate()
    assert m.compute_reduction >= 0.50


def test_aggregate_quality_preservation() -> (
    None
):
    m = aggregate()
    assert m.quality_preservation >= 0.95


def test_aggregate_tactical_miss_rate() -> None:
    m = aggregate()
    assert m.tactical_miss_rate <= 0.05


def test_aggregate_pv_stability() -> None:
    m = aggregate()
    assert m.pv_stability >= 0.90


def test_aggregate_governance_integrity() -> None:
    m = aggregate()
    assert m.search_governance_integrity >= 0.95


def test_aggregate_efficiency_gain() -> None:
    m = aggregate()
    assert m.compute_efficiency_gain >= 0.50


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
    """Pflichtfrage 5: entsteht echte
    epistemische Kompression?"""
    assert classify() == (
        ChessGovernanceClass
        .EPISTEMIC_SEARCH_COMPRESSOR
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_SEARCH_COMPRESSOR",
        "DESI_BRUTE_FORCE_DEPENDENT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_search_compressor() -> (
    None
):
    """Killerfrage: kann DESi Suchraeume
    epistemisch komprimieren, ohne relevante
    Information zu verlieren?"""
    assert build_report().recommendation == (
        "DESI_SEARCH_COMPRESSOR"
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
        c.value for c in ChessGovernanceClass
    ]
    assert "E_search_degrading" in classes
    assert (
        "A_epistemic_search_compressor"
        in classes
    )


def test_artifact_present() -> None:
    art = _load("v11_4_verdict.json")
    assert art["schema_version"] == (
        "v11_4_chess_governance_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v11_4_verdict.json")
    assert art["final_classification"] == (
        "A_epistemic_search_compressor"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v11_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v11_4_verdict.json")
    required = {
        "final_classification", "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "compute_efficiency_gain",
        "quality_preservation",
        "search_governance_integrity",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v11_4_report.json")
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
    art = _load("v11_4_verdict.json")
    live = (
        build_chess_governance_verdict_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_chess_governance_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "DESI_SEARCH_COMPRESSOR" in doc
    assert (
        "A_epistemic_search_compressor" in doc
    )
    assert "Concept Gate" in doc
    assert "compute_efficiency_gain" in doc
    assert "Pflichtfragen" in doc

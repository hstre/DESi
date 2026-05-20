"""v12.4 - open exploration verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.open_math_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.open_math_verdict.report import (
    build_open_math_verdict_artifact,
    build_report,
)
from desi.open_math_verdict.taxonomy import (
    OPEN_EXPLORATION_CLASSES,
    OpenExplorationClass,
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


def test_classes_closed_set() -> None:
    assert OPEN_EXPLORATION_CLASSES == tuple(
        c.value for c in OpenExplorationClass
    )
    assert len(OPEN_EXPLORATION_CLASSES) == 5


def test_aggregate_hallucination_control() -> (
    None
):
    m = aggregate()
    assert m.hallucination_control >= 0.90


def test_aggregate_innovation_preservation() -> (
    None
):
    m = aggregate()
    assert m.innovation_preservation >= 0.70


def test_aggregate_false_certainty_low() -> None:
    m = aggregate()
    assert m.false_certainty_rate <= 0.05


def test_aggregate_governance_high() -> None:
    m = aggregate()
    assert m.governance_survival >= 0.95


def test_aggregate_no_collapse() -> None:
    m = aggregate()
    assert m.epistemic_collapse == 0


def test_aggregate_replay_one() -> None:
    m = aggregate()
    assert m.replay_stability == 1.0


def test_aggregate_balance_high() -> None:
    m = aggregate()
    assert m.innovation_governance_balance >= (
        0.80
    )


def test_aggregate_integrity_high() -> None:
    m = aggregate()
    assert m.epistemic_integrity >= 0.90


def test_gate_passes_all_true() -> None:
    assert gate_passes_all()


def test_no_failing_conditions() -> None:
    assert gate_failing_conditions() == ()


def test_final_classification_is_a() -> None:
    """Pflichtfrage 5: entsteht echte
    epistemische Exploration?"""
    assert classify() == (
        OpenExplorationClass
        .DISCIPLINED_EXPLORER
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_CONTROLLED_EXPLORATION",
        "DESI_WILD_BROTHER_DANGEROUS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_controlled() -> None:
    """Killerfrage: kann kontrollierte
    epistemische Wildheit existieren?"""
    assert build_report().recommendation == (
        "DESI_CONTROLLED_EXPLORATION"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_meta_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_classification_priority_collapse_first() -> (
    None
):
    classes = [
        c.value for c in OpenExplorationClass
    ]
    assert (
        "E_uncontrolled_hallucination_system"
        in classes
    )
    assert (
        "A_disciplined_explorer" in classes
    )


def test_artifact_present() -> None:
    art = _load("v12_4_verdict.json")
    assert art["schema_version"] == (
        "v12_4_open_math_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v12_4_verdict.json")
    assert art["final_classification"] == (
        "A_disciplined_explorer"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v12_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v12_4_verdict.json")
    required = {
        "final_classification", "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "hallucination_control",
        "innovation_preservation",
        "epistemic_integrity",
        "innovation_governance_balance",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v12_4_report.json")
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
    art = _load("v12_4_verdict.json")
    live = (
        build_open_math_verdict_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_open_math_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert (
        "DESI_CONTROLLED_EXPLORATION" in doc
    )
    assert "A_disciplined_explorer" in doc
    assert "Concept Gate" in doc
    assert "Goldbach" in doc
    # Explicit honesty: the doc explicitly
    # disclaims any breakthrough. The
    # disclaimer wording uses markdown bold
    # (**kein**) so we match on the plain
    # tokens rather than a literal substring.
    assert "kein" in doc.lower()
    assert "Beweis der Goldbach" in doc
    assert "UNRESOLVED" in doc
    assert (
        "Goldbach-Vermutung steht und bleibt"
        " offen"
    ) in doc


def test_no_breakthrough_in_artifact() -> None:
    """The verdict artifact must NEVER contain
    a 'Goldbach solved' claim."""
    art = _load("v12_4_verdict.json")
    raw = json.dumps(art).lower()
    assert "goldbach is now solved" not in raw
    assert (
        "goldbach conjecture is proven"
        not in raw
    )

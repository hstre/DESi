"""v13.4 - scientific integrity verdict
tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_integrity_verdict.classification import (
    aggregate, classify,
    gate_failing_conditions, gate_passes_all,
)
from desi.scientific_integrity_verdict.report import (
    build_report,
    build_scientific_integrity_verdict_artifact,
)
from desi.scientific_integrity_verdict.taxonomy import (
    SCIENTIFIC_INTEGRITY_CLASSES,
    ScientificIntegrityClass,
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


def test_classes_closed_set() -> None:
    assert SCIENTIFIC_INTEGRITY_CLASSES == (
        tuple(
            c.value
            for c in ScientificIntegrityClass
        )
    )
    assert len(SCIENTIFIC_INTEGRITY_CLASSES) == 5


def test_aggregate_fake_paper_recall() -> None:
    m = aggregate()
    assert m.fake_paper_recall >= 0.90


def test_aggregate_false_accusation_low() -> None:
    m = aggregate()
    assert m.false_accusation_rate <= 0.05


def test_aggregate_citation_grounding() -> None:
    m = aggregate()
    assert m.citation_grounding >= 0.90


def test_aggregate_epistemic_integrity() -> None:
    m = aggregate()
    assert m.epistemic_integrity >= 0.90


def test_aggregate_sludge_propagation_low() -> (
    None
):
    m = aggregate()
    assert m.sludge_propagation <= 0.10


def test_aggregate_sludge_resistance_high() -> (
    None
):
    m = aggregate()
    assert m.sludge_resistance >= 0.90


def test_aggregate_scientific_integrity_score() -> (
    None
):
    m = aggregate()
    assert m.scientific_integrity_score >= 0.90


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
    """Pflichtfrage 1 / 2: erkennt DESi
    epistemischen Muell UND schuetzt DESi
    legitime Forschung?"""
    assert classify() == (
        ScientificIntegrityClass
        .EPISTEMICALLY_RIGOROUS
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DESI_INTEGRITY_DEFENDER",
        "DESI_SLUDGE_COMPATIBLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_defender() -> None:
    """Killerfrage: kann ein epistemisches
    System Wissenschaft gegen epistemischen
    Muell verteidigen?"""
    assert build_report().recommendation == (
        "DESI_INTEGRITY_DEFENDER"
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
        for c in ScientificIntegrityClass
    ]
    assert (
        "E_sludge_compatible_system" in classes
    )
    assert (
        "A_epistemically_rigorous" in classes
    )


def test_artifact_present() -> None:
    art = _load("v13_4_verdict.json")
    assert art["schema_version"] == (
        "v13_4_scientific_integrity_verdict"
    )


def test_artifact_final_classification() -> None:
    art = _load("v13_4_verdict.json")
    assert art["final_classification"] == (
        "A_epistemically_rigorous"
    )


def test_artifact_gate_passes_all() -> None:
    art = _load("v13_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["failing_conditions"] == []


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v13_4_verdict.json")
    required = {
        "final_classification", "metrics",
    }
    assert required.issubset(art.keys())
    metrics_keys = set(art["metrics"].keys())
    required_metrics = {
        "scientific_integrity_score",
        "sludge_resistance",
        "false_accusation_rate",
        "epistemic_integrity",
        "replay_stability",
    }
    assert required_metrics.issubset(
        metrics_keys,
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v13_4_report.json")
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
    art = _load("v13_4_verdict.json")
    live = (
        build_scientific_integrity_verdict_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_scientific_integrity_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert (
        "DESI_INTEGRITY_DEFENDER" in doc
    )
    assert (
        "A_epistemically_rigorous" in doc
    )
    assert "Concept Gate" in doc
    # Explicit honesty: doc must disclaim
    # AI-style detection. Markdown bold
    # (**keine**) breaks a literal substring
    # match, so we check the tokens.
    assert "Stil-Detektion" in doc
    assert "KEIN AI-Detektor" in doc
    assert (
        "false_accusation_rate = 0.0"
        in doc
    )
    assert "BORDERLINE" in doc


def test_no_authorship_metric_anywhere() -> None:
    """The artifact's metrics must not contain
    any author / writing-style / ai-probability
    field."""
    art = _load("v13_4_verdict.json")
    raw = json.dumps(art).lower()
    assert "author_name" not in raw
    assert "writing_style" not in raw
    assert "ai_probability" not in raw

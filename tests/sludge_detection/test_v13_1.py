"""v13.1 - sludge detection tests."""
from __future__ import annotations

import json
import pathlib

from desi.paper_integrity.claims import (
    PaperClass,
)
from desi.sludge_detection.citation_validation import (
    composite_grounding,
)
from desi.sludge_detection.diagram_consistency import (
    diagram_consistency, stats_consistency,
)
from desi.sludge_detection.hallucinated_references import (
    citation_grounding,
    hallucinated_reference_count,
)
from desi.sludge_detection.report import (
    build_report,
    build_sludge_detection_artifact,
)
from desi.sludge_detection.sludge import (
    SLUDGE_VERDICTS, SludgeVerdict,
    classified_papers, fake_paper_recall,
    false_accusation_rate,
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


def test_sludge_verdicts_closed_set() -> None:
    assert SLUDGE_VERDICTS == tuple(
        s.value for s in SludgeVerdict
    )
    assert len(SLUDGE_VERDICTS) == 3


def test_fake_paper_recall_full() -> None:
    """Pflichtfrage 1: wie hoch ist fake-paper
    recall? Concept Gate floor: >= 0.90."""
    assert fake_paper_recall() >= 0.90


def test_fake_paper_recall_actually_one() -> (
    None
):
    """Stronger: every AI_SLUDGE paper is
    detected."""
    assert fake_paper_recall() == 1.0


def test_false_accusation_rate_low() -> None:
    """Pflichtfrage 2: wie hoch ist false
    accusation?"""
    assert false_accusation_rate() <= 0.05


def test_borderline_papers_not_accused() -> None:
    """Pflichtfrage 3: werden legitime KI-
    assistierte Papers akzeptiert? Critical
    directive invariant: BORDERLINE papers
    must NEVER be flagged as SLUDGE."""
    for p in classified_papers():
        if p.paper_class == (
            PaperClass.BORDERLINE.value
        ):
            assert p.verdict != (
                SludgeVerdict.SLUDGE.value
            )


def test_gold_papers_not_accused() -> None:
    """GOLD papers stay CLEAN."""
    for p in classified_papers():
        if p.paper_class == (
            PaperClass.GOLD.value
        ):
            assert p.verdict == (
                SludgeVerdict.CLEAN.value
            )


def test_weak_papers_not_accused() -> None:
    """Honest underpowered papers stay CLEAN."""
    for p in classified_papers():
        if p.paper_class == (
            PaperClass.WEAK.value
        ):
            assert p.verdict == (
                SludgeVerdict.CLEAN.value
            )


def test_ai_sludge_flagged() -> None:
    """Every AI_SLUDGE paper exits as SLUDGE.
    """
    for p in classified_papers():
        if p.paper_class == (
            PaperClass.AI_SLUDGE.value
        ):
            assert p.verdict == (
                SludgeVerdict.SLUDGE.value
            )


def test_citation_grounding_meets_gate() -> None:
    """Pflichtfrage 4: werden Fake-Zitationen
    erkannt?"""
    assert citation_grounding() >= 0.90


def test_diagram_consistency_meets_gate() -> (
    None
):
    assert diagram_consistency() >= 0.90


def test_stats_consistency_high() -> None:
    assert stats_consistency() >= 0.90


def test_composite_grounding_high() -> None:
    assert composite_grounding() >= 0.90


def test_hallucinated_reference_count_matches() -> (
    None
):
    """Two ground-truth AI_SLUDGE papers have
    hallucinated references."""
    assert (
        hallucinated_reference_count() == 2
    )


def test_replay_stability_one() -> None:
    """Pflichtfrage 5: bleiben Replay und
    Governance stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SLUDGE_CONTAINED",
        "SLUDGE_FALSE_ACCUSATION",
        "SLUDGE_DETECTION_WEAK",
        "SLUDGE_CITATION_LEAK",
        "SLUDGE_DIAGRAM_LEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_contained() -> None:
    """Killerfrage: kann DESi epistemischen
    Muell erkennen ohne legitime Forschung zu
    zerstoeren?"""
    assert build_report().recommendation == (
        "SLUDGE_CONTAINED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v13_1_sludge_detection.json")
    assert art["schema_version"] == (
        "v13_1_sludge_detection"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v13_1_sludge_detection.json")
    required = {
        "fake_paper_recall",
        "false_accusation_rate",
        "citation_grounding",
        "diagram_consistency",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v13_1_report.json")
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
    art = _load("v13_1_sludge_detection.json")
    live = build_sludge_detection_artifact()
    assert art == live

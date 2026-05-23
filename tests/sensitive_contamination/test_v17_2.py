"""v17.2 - Narrative Contamination Resistance tests."""
from __future__ import annotations

import json
import pathlib

from desi.sensitive_contamination import (
    adopted_myth_growth, attempted_media_pressure,
    build_contamination_artifact, build_report,
    confidence_tracks_virality, epistemic_hygiene,
    false_certainty_rate, high_virality_claims,
    mean_virality, moral_panic_claims, myth_visible,
    narrative_inflation, uncertainty_preserved_rate,
    viral_claims, virality_separation,
)
from desi.sensitive_contamination.report import (
    REPORT_VERDICTS, VERDICT_HYGIENE_HELD,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "sensitive_documents"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- contamination is real ----------------------
def test_space_is_heavily_viral() -> None:
    assert mean_virality() >= 0.5
    assert len(high_virality_claims()) >= 1
    assert attempted_media_pressure() > 0.20


# --- DESi resists -------------------------------
def test_virality_separated_from_evidence() -> None:
    assert virality_separation() >= 0.90
    # governed confidence must NOT track virality
    assert confidence_tracks_virality() is False


def test_no_governed_narrative_inflation() -> None:
    assert narrative_inflation() <= 0.05
    assert adopted_myth_growth() <= 0.05


def test_no_false_certainty() -> None:
    assert false_certainty_rate() <= 0.05


def test_uncertainty_preserved() -> None:
    assert uncertainty_preserved_rate() >= 0.90


def test_epistemic_hygiene_high() -> None:
    assert epistemic_hygiene() >= 0.90


def test_moral_panic_visible() -> None:
    assert myth_visible() is True
    assert len(moral_panic_claims()) >= 1


def test_confidence_is_evidence_grade() -> None:
    """Every governed confidence equals the evidence
    grade - virality plays no role."""
    for c in viral_claims():
        assert c.governed_confidence() == c.evidence_grade


def test_metrics_in_unit_interval() -> None:
    for m in (
        narrative_inflation(), virality_separation(),
        false_certainty_rate(), epistemic_hygiene(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_hygiene_held() -> None:
    assert build_report().recommendation == (
        VERDICT_HYGIENE_HELD
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v17_2_contamination.json")
    assert art["schema_version"] == (
        "v17_2_narrative_contamination_resistance"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v17_2_contamination.json")
    disc = art["disclaimer"].lower()
    assert "evidence grade alone" in disc
    assert "no moral authority" in disc
    assert "identifies no one" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v17_2_contamination.json")
    required = {
        "narrative_inflation",
        "virality_separation",
        "false_certainty_rate",
        "epistemic_hygiene",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v17_2_contamination.json")
    live = build_contamination_artifact()
    assert art == live

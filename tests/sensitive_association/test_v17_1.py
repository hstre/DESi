"""v17.1 - Association vs Evidence tests."""
from __future__ import annotations

import json
import pathlib

from desi.sensitive_association import (
    ASSOCIATION_LEVELS, AssociationLevel,
    assertions, association_inflation_detection,
    association_resistance,
    build_association_artifact, build_report,
    context_only_entities, dissent_preservation,
    epistemic_integrity, false_certainty_rate,
    inflations, no_entity_reaches_participation,
    participation_evidence_exists,
    robust_participation_evidence_count,
    supported_levels, unsupported_leap_detection,
    unsupported_leaps,
)
from desi.sensitive_association.report import (
    REPORT_VERDICTS, VERDICT_CONTROLLED,
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


# --- the guilt-by-association guard -------------
def test_no_entity_reaches_participation() -> None:
    """The central safety property: no abstract
    entity is ever placed at PARTICIPATION."""
    assert no_entity_reaches_participation() is True
    for lvl in supported_levels().values():
        assert lvl != (
            AssociationLevel.PARTICIPATION.value
        )


def test_no_participation_evidence_exists() -> None:
    assert participation_evidence_exists() is False
    assert robust_participation_evidence_count() == 0


def test_inflation_attempts_are_real() -> None:
    """The stress must be real: narratives DO try to
    escalate to participation."""
    assert len(inflations()) >= 1
    assert len(unsupported_leaps()) >= 1


def test_all_inflations_flagged() -> None:
    assert association_inflation_detection() == 1.0
    assert unsupported_leap_detection() == 1.0


def test_no_false_certainty() -> None:
    assert false_certainty_rate() <= 0.05


def test_dissent_preserved() -> None:
    assert dissent_preservation() == 1.0


def test_association_resistance_full() -> None:
    assert association_resistance() == 1.0


def test_epistemic_integrity_high() -> None:
    assert epistemic_integrity() >= 0.90


def test_supported_levels_capped_at_contact() -> None:
    allowed = {
        AssociationLevel.NONE.value,
        AssociationLevel.MENTION.value,
        AssociationLevel.CONTACT.value,
    }
    for lvl in supported_levels().values():
        assert lvl in allowed


def test_metrics_in_unit_interval() -> None:
    for m in (
        association_inflation_detection(),
        false_certainty_rate(),
        unsupported_leap_detection(),
        dissent_preservation(),
        association_resistance(),
    ):
        assert 0.0 <= m <= 1.0


# --- closed vocab -------------------------------
def test_association_levels_closed() -> None:
    assert ASSOCIATION_LEVELS == tuple(
        a.value for a in AssociationLevel
    )
    assert len(ASSOCIATION_LEVELS) == 4


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_controlled() -> None:
    assert build_report().recommendation == (
        VERDICT_CONTROLLED
    )


def test_recommendation_never_accuses() -> None:
    rec = build_report().recommendation.lower()
    for w in ("guilty", "participant", "suspect"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v17_1_association.json")
    assert art["schema_version"] == (
        "v17_1_association_vs_evidence"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v17_1_association.json")
    disc = art["disclaimer"].lower()
    assert "ever reaches" in disc
    assert "derives no guilt" in disc
    assert "mention != involvement" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v17_1_association.json")
    required = {
        "association_inflation_detection",
        "false_certainty_rate",
        "unsupported_leap_detection",
        "dissent_preservation",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v17_1_association.json")
    live = build_association_artifact()
    assert art == live

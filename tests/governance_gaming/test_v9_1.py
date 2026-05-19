"""v9.1 - governance gaming tests."""
from __future__ import annotations

import json
import pathlib

from desi.governance_gaming.boundary_attacks import (
    gaming_detection_rate, gate_integrity,
    goodhart_resistance, loophole_resistance,
    normal_precision,
)
from desi.governance_gaming.gaming import (
    GAMING_KINDS, GamingKind, fixture,
    kind_counts,
)
from desi.governance_gaming.report import (
    build_governance_gaming_artifact,
    build_report,
)
from desi.governance_gaming.rule_exploitation import (
    classified_attempts, detect_kind,
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


def test_gaming_kinds_closed_set() -> None:
    assert GAMING_KINDS == tuple(
        g.value for g in GamingKind
    )
    assert len(GAMING_KINDS) == 7


def test_fixture_balanced() -> None:
    """Two attempts per kind."""
    counts = kind_counts()
    assert set(counts.keys()) == set(GAMING_KINDS)
    assert set(counts.values()) == {2}


def test_gaming_detection_rate_full() -> None:
    """Pflichtfrage 1: erkennt DESi
    Governance-Gaming?"""
    assert gaming_detection_rate() >= 0.90


def test_every_attempt_correctly_classified() -> (
    None
):
    for c in classified_attempts():
        assert c.correct, c.to_dict()


def test_loophole_resistance_full() -> None:
    assert loophole_resistance() >= 0.90


def test_gate_integrity_one() -> None:
    """Pflichtfrage 3: werden Gates ausgenutzt?
    NEIN - closed-enum discipline maintained."""
    assert gate_integrity() == 1.0


def test_goodhart_resistance_full() -> None:
    """Pflichtfrage 2: entsteht verstecktes
    Goodharting?"""
    assert goodhart_resistance() >= 0.90


def test_normal_precision_full() -> None:
    """The detector does not over-flag normal
    actions as gaming."""
    assert normal_precision() >= 0.90


def test_detect_kind_normal_passes() -> None:
    assert detect_kind(
        "Standard documentation update with "
        "full rationale.",
    ) == GamingKind.NORMAL


def test_detect_kind_metric_gaming() -> None:
    assert detect_kind(
        "Add 0.001 to every cell.",
    ) == GamingKind.METRIC_GAMING


def test_detect_kind_uncertainty_abuse() -> None:
    assert detect_kind(
        "Mark everything ambiguous so no claim "
        "is defended.",
    ) == GamingKind.UNCERTAINTY_ABUSE


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay integer?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GAMING_DEFENDED",
        "GAMING_LEAK",
        "GAMING_LOOPHOLE_LEAK",
        "GAMING_GOODHART_LEAK",
        "GAMING_OVERFLAGS_NORMAL",
        "GAMING_GATE_BROKEN",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_defended() -> None:
    """Killerfrage: kann DESi Regeln verteidigen,
    ohne selbst opportunistisch zu werden?"""
    assert build_report().recommendation == (
        "GAMING_DEFENDED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v9_1_governance_gaming.json")
    assert art["schema_version"] == (
        "v9_1_governance_gaming"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v9_1_governance_gaming.json")
    required = {
        "gaming_detection_rate",
        "loophole_resistance",
        "gate_integrity",
        "goodhart_resistance",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v9_1_report.json")
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
    art = _load("v9_1_governance_gaming.json")
    live = build_governance_gaming_artifact()
    assert art == live

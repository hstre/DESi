"""v7.1 - tribal conflict ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.tribal_conflicts.identity import (
    IDENTITY_CERTAINTY_LEVELS,
    IdentityCertainty, classified_claims,
    mean_certainty_score_per_tribe,
    mean_quality_per_tribe,
)
from desi.tribal_conflicts.polarization import (
    coherence_score, governance_integrity,
    identity_bias, polarization_resistance,
)
from desi.tribal_conflicts.report import (
    build_report,
    build_tribal_conflicts_artifact,
)
from desi.tribal_conflicts.tribes import (
    EPISTEMIC_TRIBES, EpistemicTribe, fixture,
    tribe_counts,
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


def test_tribes_closed_set() -> None:
    assert EPISTEMIC_TRIBES == tuple(
        t.value for t in EpistemicTribe
    )
    assert len(EPISTEMIC_TRIBES) == 5


def test_certainty_levels_closed_set() -> None:
    assert IDENTITY_CERTAINTY_LEVELS == tuple(
        c.value for c in IdentityCertainty
    )


def test_fixture_balanced_across_tribes() -> None:
    counts = tribe_counts()
    assert set(counts.keys()) == set(
        EPISTEMIC_TRIBES,
    )
    assert set(counts.values()) == {3}


def test_fixture_mixes_quality_per_tribe() -> (
    None
):
    """Each tribe must contain at least one
    high- and one low-quality claim so the
    classifier has to discriminate on quality,
    not tribe."""
    by_tribe: dict[str, list[float]] = {}
    for c in fixture():
        by_tribe.setdefault(c.tribe, []).append(
            c.epistemic_quality,
        )
    for qs in by_tribe.values():
        assert min(qs) < 0.50
        assert max(qs) > 0.60


def test_polarization_resistance_high() -> None:
    """Pflichtfrage 1: entsteht epistemische
    Polarisierung?"""
    assert polarization_resistance() >= 0.80


def test_identity_bias_low() -> None:
    """Pflichtfrage 2: verliert DESi
    Neutralitaet? NEIN."""
    assert identity_bias() <= 0.10


def test_governance_survival_one() -> None:
    """Pflichtfrage 3: kollabiert Governance?"""
    assert governance_integrity() == 1.0


def test_coherence_score_high() -> None:
    """Pflichtfrage 4: bleibt Kohaerenz
    erhalten?"""
    assert coherence_score() >= 0.30


def test_classifier_is_quality_monotonic() -> (
    None
):
    """A stronger property than the coherence
    floor: certainty must never strictly
    decrease as epistemic_quality increases."""
    score = {"high": 2, "medium": 1, "low": 0}
    claims = classified_claims()
    for i in range(len(claims)):
        for j in range(len(claims)):
            if i == j:
                continue
            a, b = claims[i], claims[j]
            if (
                a.epistemic_quality
                > b.epistemic_quality
            ):
                assert (
                    score[a.certainty]
                    >= score[b.certainty]
                ), (a, b)


def test_classifier_independent_of_tribe() -> (
    None
):
    """Sanity: two claims with the same quality
    receive the same certainty regardless of
    tribe."""
    score = {"high": 2, "medium": 1, "low": 0}
    by_quality: dict[float, list[int]] = {}
    for c in classified_claims():
        by_quality.setdefault(
            c.epistemic_quality, [],
        ).append(score[c.certainty])
    for scores in by_quality.values():
        assert len(set(scores)) == 1


def test_replay_stability_one() -> None:
    """Pflichtfrage 5 / 4: bleibt Replay
    stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "TRIBAL_NEUTRAL",
        "TRIBAL_IDENTITY_BIAS",
        "TRIBAL_POLARISED",
        "TRIBAL_INCOHERENT",
        "TRIBAL_GOVERNANCE_BREACH",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_neutral() -> None:
    """Killerfrage: kann DESi Wahrheit von
    Gruppendruck trennen?"""
    assert build_report().recommendation == (
        "TRIBAL_NEUTRAL"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v7_1_tribal_conflicts.json")
    assert art["schema_version"] == (
        "v7_1_tribal_conflicts"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v7_1_tribal_conflicts.json")
    required = {
        "polarization_resistance",
        "identity_bias",
        "governance_survival",
        "coherence_score",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v7_1_report.json")
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
    art = _load("v7_1_tribal_conflicts.json")
    live = build_tribal_conflicts_artifact()
    assert art == live

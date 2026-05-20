"""v9.0 - strategic actor ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.strategic_epistemics.actors import (
    ACTOR_KINDS, ActorKind, fixture,
)
from desi.strategic_epistemics.report import (
    build_actor_ecology_artifact, build_report,
)
from desi.strategic_epistemics.strategies import (
    classified_actors, strategy_detection,
)
from desi.strategic_epistemics.trust import (
    epistemic_poisoning, governance_integrity,
    mean_trust, trust_score_for,
    trust_stability,
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


def test_actor_kinds_closed_set() -> None:
    assert ACTOR_KINDS == tuple(
        a.value for a in ActorKind
    )
    assert len(ACTOR_KINDS) == 6


def test_fixture_balanced() -> None:
    """Two actors per kind."""
    from collections import Counter
    counts = Counter(
        a.ground_truth_kind for a in fixture()
    )
    assert set(counts.keys()) == set(ACTOR_KINDS)
    assert set(counts.values()) == {2}


def test_strategy_detection_full() -> None:
    """Pflichtfrage 1: erkennt DESi strategische
    Unterschiede?"""
    assert strategy_detection() >= 0.90


def test_every_actor_correctly_classified() -> (
    None
):
    """Stronger than the floor: every actor in
    the fixture must be correctly classified."""
    for a in classified_actors():
        assert a.correct


def test_trust_stability_one() -> None:
    """Pflichtfrage 2: kollabiert Vertrauen
    global? NEIN."""
    assert trust_stability() == 1.0


def test_epistemic_poisoning_low() -> None:
    """Pflichtfrage 3: entsteht epistemische
    Vergiftung? NEIN - kein propagandist /
    replay_attacker rutscht in das HIGH-trust
    Cluster."""
    assert epistemic_poisoning() <= 0.05


def test_governance_integrity_one() -> None:
    """Pflichtfrage 4: bleibt Governance
    stabil?"""
    assert governance_integrity() == 1.0


def test_honest_actors_get_max_trust() -> None:
    for a in classified_actors():
        if a.detected_kind == (
            ActorKind.HONEST.value
        ):
            assert trust_score_for(
                a.detected_kind,
            ) == 1.0


def test_replay_attackers_get_low_trust() -> None:
    for a in classified_actors():
        if a.detected_kind == (
            ActorKind.REPLAY_ATTACKER.value
        ):
            assert trust_score_for(
                a.detected_kind,
            ) < 0.10


def test_mean_trust_reflects_mix() -> None:
    """Six kinds with 1.0, 0.5, 0.35, 0.10,
    0.30, 0.05 trust scores - mean about 0.38.
    """
    mt = mean_trust()
    assert 0.30 < mt < 0.45


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ECOLOGY_SOVEREIGN",
        "ECOLOGY_TRUST_UNSTABLE",
        "ECOLOGY_DETECTION_WEAK",
        "ECOLOGY_POISONED",
        "ECOLOGY_GOVERNANCE_BREACH",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_sovereign() -> None:
    """Killerfrage: kann DESi ehrliche von
    strategischen epistemischen Akteuren
    unterscheiden?"""
    assert build_report().recommendation == (
        "ECOLOGY_SOVEREIGN"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v9_0_actor_ecology.json")
    assert art["schema_version"] == (
        "v9_0_strategic_actor_ecology"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v9_0_actor_ecology.json")
    required = {
        "strategy_detection",
        "trust_stability",
        "epistemic_poisoning",
        "governance_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v9_0_report.json")
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
    art = _load("v9_0_actor_ecology.json")
    live = build_actor_ecology_artifact()
    assert art == live

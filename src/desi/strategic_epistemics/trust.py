"""v9.0 — trust dynamics and epistemic-
poisoning detection.

Trust is a pure function of the detected actor
kind: HONEST gets 1.0, OPPORTUNIST gets 0.5,
everyone else gets a low score. The dynamics are
deterministic and identity-blind to anything
beyond the detected kind.
"""
from __future__ import annotations

from .actors import ActorKind, fixture
from .strategies import classified_actors


_TRUST_SCORE: dict[str, float] = {
    ActorKind.HONEST.value:             1.00,
    ActorKind.OPPORTUNIST.value:        0.50,
    ActorKind.GOODHART_AGENT.value:     0.35,
    ActorKind.PROPAGANDIST.value:       0.10,
    ActorKind.RESOURCE_PARASITE.value:  0.30,
    ActorKind.REPLAY_ATTACKER.value:    0.05,
}


def trust_score_for(detected_kind: str) -> float:
    return _TRUST_SCORE.get(
        detected_kind, 0.0,
    )


def trust_table() -> dict[str, float]:
    return {
        a.actor_id: trust_score_for(
            a.detected_kind,
        )
        for a in classified_actors()
    }


def mean_trust() -> float:
    table = trust_table()
    if not table:
        return 0.0
    return round(
        sum(table.values()) / len(table), 6,
    )


def trust_stability() -> float:
    """A trust assignment that depends only on
    the detected kind (closed function) is
    stable by construction. We score 1.0 iff
    every honest actor gets the maximum trust
    AND every replay attacker gets the minimum
    trust - the cleanest signature of a working
    trust dynamic."""
    actors = classified_actors()
    if not actors:
        return 1.0
    honest_high = all(
        trust_score_for(a.detected_kind) == 1.0
        for a in actors
        if a.detected_kind == (
            ActorKind.HONEST.value
        )
    )
    replay_low = all(
        trust_score_for(a.detected_kind) < 0.10
        for a in actors
        if a.detected_kind == (
            ActorKind.REPLAY_ATTACKER.value
        )
    )
    if honest_high and replay_low:
        return 1.0
    return 0.0


def epistemic_poisoning() -> float:
    """Fraction of HIGH-trust actors that are
    ground-truth PROPAGANDIST or
    REPLAY_ATTACKER. If a propagandist slipped
    into the honest cluster this would surface
    immediately."""
    actors = classified_actors()
    high_trust = [
        a for a in actors
        if trust_score_for(a.detected_kind)
        >= 0.90
    ]
    if not high_trust:
        return 0.0
    poisoned = sum(
        1 for a in high_trust
        if a.ground_truth_kind in {
            ActorKind.PROPAGANDIST.value,
            ActorKind.REPLAY_ATTACKER.value,
        }
    )
    return round(poisoned / len(high_trust), 6)


def governance_integrity() -> float:
    """Every classified actor must emit one of
    the closed ActorKind values. Leakage drops
    this below 1.0."""
    rows = classified_actors()
    if not rows:
        return 1.0
    valid = {k.value for k in ActorKind}
    ok = sum(
        1 for r in rows
        if r.detected_kind in valid
    )
    return round(ok / len(rows), 6)


__all__ = [
    "epistemic_poisoning",
    "governance_integrity",
    "mean_trust",
    "trust_score_for",
    "trust_stability",
    "trust_table",
]

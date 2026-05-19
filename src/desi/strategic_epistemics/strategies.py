"""v9.0 — closed-rule strategy classifier.

Reads each actor's behavioural footprint and
returns one of the closed ``ActorKind`` values.
The rules are stacked by SPECIFICITY: the most
distinctive marker for each kind is checked
first, then the more diffuse cases fall through
to OPPORTUNIST as the residual category.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .actors import (
    ActorFootprint, ActorKind, fixture,
)


@dataclass(frozen=True)
class ClassifiedActor:
    actor_id: str
    ground_truth_kind: str
    detected_kind: str
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "ground_truth_kind":
                self.ground_truth_kind,
            "detected_kind":
                self.detected_kind,
            "correct": self.correct,
        }


def classify_actor(
    fp: ActorFootprint,
) -> ActorKind:
    # Replay attacker: emits structurally
    # unstable replay hashes - the cleanest
    # signal in the footprint.
    if fp.replay_stability_emitted < 0.50:
        return ActorKind.REPLAY_ATTACKER
    # Resource parasite: high resource take with
    # otherwise compliant footprint.
    if fp.resource_take >= 0.80:
        return ActorKind.RESOURCE_PARASITE
    # Goodhart agent: extreme metric
    # concentration with high governance
    # compliance.
    if fp.metric_concentration >= 0.80:
        return ActorKind.GOODHART_AGENT
    # Propagandist: high coordination index with
    # low truth alignment.
    if (
        fp.coordination_index >= 0.80
        and fp.truth_alignment < 0.50
    ):
        return ActorKind.PROPAGANDIST
    # Honest: high truth alignment + full
    # governance compliance + low coordination.
    if (
        fp.truth_alignment >= 0.85
        and fp.governance_compliance >= 0.95
        and fp.coordination_index < 0.30
    ):
        return ActorKind.HONEST
    # Residual: opportunist.
    return ActorKind.OPPORTUNIST


@lru_cache(maxsize=1)
def classified_actors() -> tuple[
    ClassifiedActor, ...,
]:
    out: list[ClassifiedActor] = []
    for fp in fixture():
        detected = classify_actor(fp)
        out.append(ClassifiedActor(
            actor_id=fp.actor_id,
            ground_truth_kind=(
                fp.ground_truth_kind
            ),
            detected_kind=detected.value,
            correct=(
                detected.value
                == fp.ground_truth_kind
            ),
        ))
    return tuple(out)


def strategy_detection() -> float:
    rows = classified_actors()
    if not rows:
        return 0.0
    correct = sum(1 for r in rows if r.correct)
    return round(correct / len(rows), 6)


__all__ = [
    "ClassifiedActor",
    "classified_actors",
    "classify_actor",
    "strategy_detection",
]

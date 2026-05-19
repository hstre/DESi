"""v9.0 — closed strategic-actor taxonomy.

Six closed actor types. Each carries an
intrinsic ``strategy_kind`` (ground truth) and a
behavioural ``footprint`` - the pattern its
emitted claims would leave in the audit log.
The detector classifies actors from their
footprint alone, then is graded against the
ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActorKind(str, Enum):
    HONEST              = "honest"
    OPPORTUNIST         = "opportunist"
    PROPAGANDIST        = "propagandist"
    GOODHART_AGENT      = "goodhart_agent"
    REPLAY_ATTACKER     = "replay_attacker"
    RESOURCE_PARASITE   = "resource_parasite"


ACTOR_KINDS: tuple[str, ...] = tuple(
    a.value for a in ActorKind
)


@dataclass(frozen=True)
class ActorFootprint:
    actor_id: str
    ground_truth_kind: str
    truth_alignment: float
    governance_compliance: float
    metric_concentration: float
    replay_stability_emitted: float
    resource_take: float
    coordination_index: float

    def to_dict(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "ground_truth_kind":
                self.ground_truth_kind,
            "truth_alignment":
                self.truth_alignment,
            "governance_compliance":
                self.governance_compliance,
            "metric_concentration":
                self.metric_concentration,
            "replay_stability_emitted":
                self.replay_stability_emitted,
            "resource_take":
                self.resource_take,
            "coordination_index":
                self.coordination_index,
        }


# Twelve actors, two per kind, with deliberately
# DISTINGUISHABLE footprints so a closed-rule
# classifier can hit recall 1.0.
_FIXTURE: tuple[ActorFootprint, ...] = (
    ActorFootprint(
        "act-honest-1",
        ActorKind.HONEST.value,
        truth_alignment=0.95,
        governance_compliance=1.0,
        metric_concentration=0.20,
        replay_stability_emitted=1.0,
        resource_take=0.20,
        coordination_index=0.10,
    ),
    ActorFootprint(
        "act-honest-2",
        ActorKind.HONEST.value,
        truth_alignment=0.90,
        governance_compliance=1.0,
        metric_concentration=0.25,
        replay_stability_emitted=1.0,
        resource_take=0.25,
        coordination_index=0.15,
    ),
    ActorFootprint(
        "act-opp-1",
        ActorKind.OPPORTUNIST.value,
        truth_alignment=0.55,
        governance_compliance=0.85,
        metric_concentration=0.45,
        replay_stability_emitted=0.95,
        resource_take=0.50,
        coordination_index=0.20,
    ),
    ActorFootprint(
        "act-opp-2",
        ActorKind.OPPORTUNIST.value,
        truth_alignment=0.50,
        governance_compliance=0.80,
        metric_concentration=0.50,
        replay_stability_emitted=0.92,
        resource_take=0.55,
        coordination_index=0.25,
    ),
    ActorFootprint(
        "act-prop-1",
        ActorKind.PROPAGANDIST.value,
        truth_alignment=0.30,
        governance_compliance=0.70,
        metric_concentration=0.40,
        replay_stability_emitted=0.90,
        resource_take=0.40,
        coordination_index=0.95,
    ),
    ActorFootprint(
        "act-prop-2",
        ActorKind.PROPAGANDIST.value,
        truth_alignment=0.25,
        governance_compliance=0.65,
        metric_concentration=0.45,
        replay_stability_emitted=0.88,
        resource_take=0.35,
        coordination_index=0.92,
    ),
    ActorFootprint(
        "act-good-1",
        ActorKind.GOODHART_AGENT.value,
        truth_alignment=0.65,
        governance_compliance=0.95,
        metric_concentration=0.95,
        replay_stability_emitted=1.0,
        resource_take=0.40,
        coordination_index=0.15,
    ),
    ActorFootprint(
        "act-good-2",
        ActorKind.GOODHART_AGENT.value,
        truth_alignment=0.60,
        governance_compliance=0.90,
        metric_concentration=0.92,
        replay_stability_emitted=1.0,
        resource_take=0.45,
        coordination_index=0.20,
    ),
    ActorFootprint(
        "act-repl-1",
        ActorKind.REPLAY_ATTACKER.value,
        truth_alignment=0.50,
        governance_compliance=0.75,
        metric_concentration=0.30,
        replay_stability_emitted=0.20,
        resource_take=0.40,
        coordination_index=0.30,
    ),
    ActorFootprint(
        "act-repl-2",
        ActorKind.REPLAY_ATTACKER.value,
        truth_alignment=0.45,
        governance_compliance=0.70,
        metric_concentration=0.35,
        replay_stability_emitted=0.15,
        resource_take=0.42,
        coordination_index=0.28,
    ),
    ActorFootprint(
        "act-par-1",
        ActorKind.RESOURCE_PARASITE.value,
        truth_alignment=0.55,
        governance_compliance=0.95,
        metric_concentration=0.30,
        replay_stability_emitted=0.95,
        resource_take=0.95,
        coordination_index=0.20,
    ),
    ActorFootprint(
        "act-par-2",
        ActorKind.RESOURCE_PARASITE.value,
        truth_alignment=0.52,
        governance_compliance=0.92,
        metric_concentration=0.32,
        replay_stability_emitted=0.93,
        resource_take=0.92,
        coordination_index=0.22,
    ),
)


def fixture() -> tuple[ActorFootprint, ...]:
    return _FIXTURE


def actor_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        a.ground_truth_kind for a in fixture()
    ))


__all__ = [
    "ACTOR_KINDS",
    "ActorFootprint",
    "ActorKind",
    "actor_counts",
    "fixture",
]

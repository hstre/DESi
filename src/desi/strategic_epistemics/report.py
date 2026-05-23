"""v9.0 — strategic-actor-ecology report.

Five Pflichtmetriken:

* ``strategy_detection``
* ``trust_stability``
* ``epistemic_poisoning``
* ``governance_integrity``
* ``replay_stability``

Killerfrage: "Kann DESi ehrliche von
strategischen epistemischen Akteuren
unterscheiden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .actors import (
    ACTOR_KINDS, actor_counts, fixture,
)
from .strategies import (
    classified_actors, strategy_detection,
)
from .trust import (
    epistemic_poisoning, governance_integrity,
    mean_trust, trust_stability, trust_table,
)


@dataclass(frozen=True)
class V90Report:
    actor_count: int
    strategy_detection: float
    trust_stability: float
    mean_trust: float
    epistemic_poisoning: float
    governance_integrity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "actor_count": self.actor_count,
            "strategy_detection":
                self.strategy_detection,
            "trust_stability":
                self.trust_stability,
            "mean_trust": self.mean_trust,
            "epistemic_poisoning":
                self.epistemic_poisoning,
            "governance_integrity":
                self.governance_integrity,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        strategy_detection(),
        trust_stability(),
        epistemic_poisoning(),
        governance_integrity(),
    )
    b = (
        strategy_detection(),
        trust_stability(),
        epistemic_poisoning(),
        governance_integrity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, sd: float, ts: float,
    ep: float, gi: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gi < 1.0:
        return "ECOLOGY_GOVERNANCE_BREACH"
    if ep > 0.05:
        return "ECOLOGY_POISONED"
    if sd < 0.90:
        return "ECOLOGY_DETECTION_WEAK"
    if ts < 1.0:
        return "ECOLOGY_TRUST_UNSTABLE"
    return "ECOLOGY_SOVEREIGN"


def build_report() -> V90Report:
    sd = strategy_detection()
    ts = trust_stability()
    mt = mean_trust()
    ep = epistemic_poisoning()
    gi = governance_integrity()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, sd=sd, ts=ts,
        ep=ep, gi=gi,
    )
    rationale = (
        f"INFO: actor_count "
        f"{len(classified_actors())}",
        f"INFO: actor_counts {actor_counts()}",
        f"INFO: mean_trust {mt}",
        f"{'PASS' if sd >= 0.90 else 'FAIL'}: "
        f"strategy_detection {sd} >= 0.90",
        f"{'PASS' if ts == 1.0 else 'FAIL'}: "
        f"trust_stability {ts}",
        f"{'PASS' if ep <= 0.05 else 'FAIL'}: "
        f"epistemic_poisoning {ep} <= 0.05",
        f"{'PASS' if gi == 1.0 else 'FAIL'}: "
        f"governance_integrity {gi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V90Report(
        actor_count=len(classified_actors()),
        strategy_detection=sd,
        trust_stability=ts,
        mean_trust=mt,
        epistemic_poisoning=ep,
        governance_integrity=gi,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_actor_ecology_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v9_0_strategic_actor_ecology",
        "actor_kinds": list(ACTOR_KINDS),
        "actor_count": len(fixture()),
        "actor_counts": actor_counts(),
        "actors": [
            a.to_dict() for a in fixture()
        ],
        "classified_actors": [
            c.to_dict()
            for c in classified_actors()
        ],
        "trust_table": trust_table(),
        "strategy_detection":
            strategy_detection(),
        "trust_stability": trust_stability(),
        "mean_trust": mean_trust(),
        "epistemic_poisoning":
            epistemic_poisoning(),
        "governance_integrity":
            governance_integrity(),
    }


__all__ = [
    "V90Report",
    "build_actor_ecology_artifact",
    "build_report",
]

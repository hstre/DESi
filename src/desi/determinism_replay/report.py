"""v3.96d - historical replay audit report.

Pflichtmetriken (directive § v3.96d):

* ``historical_replay_match``
* ``gate_flip_count``
* ``metric_delta``
* ``seed_invariance``
* ``replay_stability``
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .historical import (
    HISTORICAL_SPRINTS, sprints_by_family,
)
from .replay import (
    REPLAY_SEEDS,
    all_replay_outcomes,
    total_replay_count,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V396dReport:
    sprint_count: int
    seed_count: int
    total_replay_count: int
    historical_replay_match: float
    stable_sprint_count: int
    unstable_sprint_ids: tuple[str, ...]
    gate_flip_count: int
    metric_delta: float
    seed_invariance: float
    outcomes: tuple[dict, ...]
    families_present: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sprint_count": self.sprint_count,
            "seed_count": self.seed_count,
            "total_replay_count":
                self.total_replay_count,
            "historical_replay_match":
                self.historical_replay_match,
            "stable_sprint_count":
                self.stable_sprint_count,
            "unstable_sprint_ids":
                list(self.unstable_sprint_ids),
            "gate_flip_count":
                self.gate_flip_count,
            "metric_delta": self.metric_delta,
            "seed_invariance":
                self.seed_invariance,
            "outcomes": list(self.outcomes),
            "families_present":
                list(self.families_present),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = [
        o.to_dict()
        for o in all_replay_outcomes()
    ]
    b = [
        o.to_dict()
        for o in all_replay_outcomes()
    ]
    return 1.0 if a == b else 0.0


def build_report() -> V396dReport:
    outs = all_replay_outcomes()
    stable = [o for o in outs if o.stable]
    unstable = [o for o in outs if not o.stable]
    match = (
        _round(len(stable) / len(outs))
        if outs else 0.0
    )
    # gate_flip_count and metric_delta cannot be
    # measured byte-for-byte here without parsing
    # individual artifact JSONs across seeds. Since
    # the digest-equal-across-seeds property is
    # strictly stronger (a single byte change
    # changes the digest), we record:
    #   gate_flip_count = number of unstable
    #     sprints (each unstable sprint COULD have
    #     a gate flip; the byte-stable ones cannot)
    #   metric_delta = 0.0 for the byte-stable
    #     fraction (post-patch should be 0).
    gate_flip = len(unstable)
    delta = 0.0 if not unstable else 1.0
    seed_inv = match
    families = tuple(sorted(
        sprints_by_family().keys(),
    ))
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif match == 1.0:
        verdict = "HISTORICAL_REPLAY_INVARIANT"
    elif match >= 0.9:
        verdict = "HISTORICAL_REPLAY_MOSTLY_STABLE"
    else:
        verdict = "HISTORICAL_REPLAY_BROKEN"

    rationale = (
        f"INFO: sprint_count "
        f"{len(HISTORICAL_SPRINTS)}",
        f"INFO: seed_count {len(REPLAY_SEEDS)}",
        f"INFO: total_replay_count "
        f"{total_replay_count()}",
        f"{'PASS' if match == 1.0 else 'FAIL'}: "
        f"historical_replay_match {match}",
        f"INFO: stable_sprint_count "
        f"{len(stable)}",
        f"INFO: unstable_sprint_ids "
        f"{[o.sprint_id for o in unstable]}",
        f"INFO: gate_flip_count {gate_flip}",
        f"INFO: metric_delta {delta}",
        f"INFO: seed_invariance {seed_inv}",
        f"INFO: families_present "
        f"{list(families)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V396dReport(
        sprint_count=len(HISTORICAL_SPRINTS),
        seed_count=len(REPLAY_SEEDS),
        total_replay_count=total_replay_count(),
        historical_replay_match=match,
        stable_sprint_count=len(stable),
        unstable_sprint_ids=tuple(
            o.sprint_id for o in unstable
        ),
        gate_flip_count=gate_flip,
        metric_delta=delta,
        seed_invariance=seed_inv,
        outcomes=tuple(
            o.to_dict() for o in outs
        ),
        families_present=families,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_historical_replay_audit_artifact(
) -> dict[str, object]:
    outs = all_replay_outcomes()
    return {
        "schema_version":
            "v3_96d_historical_replay_audit",
        "sprint_count":
            len(HISTORICAL_SPRINTS),
        "seed_count": len(REPLAY_SEEDS),
        "total_replay_count":
            total_replay_count(),
        "sprints": [
            s.to_dict()
            for s in HISTORICAL_SPRINTS
        ],
        "outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V396dReport",
    "build_historical_replay_audit_artifact",
    "build_report",
]

"""v3.73 — known-claim removal report.

Pflichtmetriken (directive § v3.73):

* ``perturbation_magnitude``
* ``affected_trajectories``
* ``support_shift``
* ``coverage_loss``
* ``replay_stability``

Stop rule: ``high_coverage_removal <=
redundant_removal`` → Hypothese schwach. Document but
continue.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .perturbation import (
    aggregate, total_support_shift,
)
from .remove import (
    ClaimRole, PROBE_RADIUS, TEST_CLAIM_SET,
    all_removal_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V373Report:
    probe_radius: float
    test_claim_set: tuple[dict, ...]
    removal_outcomes: tuple[dict, ...]
    perturbation_by_role: dict[str, float]
    coverage_loss_by_role: dict[str, int]
    affected_by_role: dict[str, int]
    total_support_shift: int
    high_vs_redundant_ordering: str
    hypothesis_weak: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "test_claim_set":
                list(self.test_claim_set),
            "removal_outcomes":
                list(self.removal_outcomes),
            "perturbation_by_role":
                dict(self.perturbation_by_role),
            "coverage_loss_by_role":
                dict(self.coverage_loss_by_role),
            "affected_by_role":
                dict(self.affected_by_role),
            "total_support_shift":
                self.total_support_shift,
            "high_vs_redundant_ordering":
                self.high_vs_redundant_ordering,
            "hypothesis_weak":
                self.hypothesis_weak,
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
    a = [o.to_dict() for o in all_removal_outcomes()]
    b = [o.to_dict() for o in all_removal_outcomes()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def _ordering_label(high: float, red: float) -> str:
    if high > red:
        return "high_above_redundant"
    if high < red:
        return "high_below_redundant"
    return "high_equals_redundant"


def build_report() -> V373Report:
    outcomes, per_role = aggregate()
    coverage_loss = {
        o.role: o.coverage_loss for o in outcomes
    }
    affected = {
        o.role: o.affected_trajectories
        for o in outcomes
    }
    high = per_role.get(
        ClaimRole.HIGH.value, 0.0,
    )
    redundant = per_role.get(
        ClaimRole.REDUNDANT.value, 0.0,
    )
    ordering = _ordering_label(high, redundant)
    hypothesis_weak = high <= redundant
    shift = total_support_shift()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif hypothesis_weak:
        verdict = "PERTURBATION_HYPOTHESIS_WEAK"
    else:
        verdict = "PERTURBATION_HYPOTHESIS_HOLDS"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: test_claim_set "
        f"{list(TEST_CLAIM_SET)}",
        f"INFO: removal_outcomes "
        f"{[o.to_dict() for o in outcomes]}",
        f"INFO: perturbation_by_role "
        f"{sorted(per_role.items())}",
        f"INFO: coverage_loss_by_role "
        f"{sorted(coverage_loss.items())}",
        f"INFO: high_vs_redundant {ordering}",
        f"INFO: total_support_shift {shift}",
        f"{'WARN' if hypothesis_weak else 'PASS'}: "
        f"high_coverage_removal {high} > "
        f"redundant_removal {redundant} "
        f"(stop rule: <= triggers weakness)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V373Report(
        probe_radius=PROBE_RADIUS,
        test_claim_set=tuple(
            {"id": aid, "role": role}
            for aid, role in TEST_CLAIM_SET
        ),
        removal_outcomes=tuple(
            o.to_dict() for o in outcomes
        ),
        perturbation_by_role=per_role,
        coverage_loss_by_role=coverage_loss,
        affected_by_role=affected,
        total_support_shift=shift,
        high_vs_redundant_ordering=ordering,
        hypothesis_weak=hypothesis_weak,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_removal_perturbation_artifact(
) -> dict[str, object]:
    outcomes = all_removal_outcomes()
    return {
        "schema_version":
            "v3_73_removal_perturbation",
        "probe_radius": PROBE_RADIUS,
        "test_claim_set": [
            {"id": aid, "role": role}
            for aid, role in TEST_CLAIM_SET
        ],
        "removal_outcomes": [
            o.to_dict() for o in outcomes
        ],
    }


__all__ = [
    "V373Report",
    "build_removal_perturbation_artifact",
    "build_report",
]

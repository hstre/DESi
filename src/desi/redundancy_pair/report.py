"""v3.78 — redundant pair removal report.

Pflichtmetriken (directive § v3.78):

* ``single_removal_perturbation``
* ``double_removal_perturbation``
* ``redundancy_unmasking_gain``
* ``unrelated_pair_perturbation``
* ``replay_stability``

Concept gate #1 / #2 contribution: single == 0 AND
double > 0 are the unmasking signals.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .removal import (
    HIGH_PAIR_A, HIGH_PAIR_B, RemovalCondition,
    UNRELATED_A, UNRELATED_B, all_conditions,
    redundancy_unmasking_gain,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V378Report:
    conditions: tuple[dict, ...]
    single_removal_perturbation: dict[str, int]
    double_removal_perturbation: int
    redundancy_unmasking_gain: int
    unrelated_pair_perturbation: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "conditions": list(self.conditions),
            "single_removal_perturbation":
                dict(self.single_removal_perturbation),
            "double_removal_perturbation":
                self.double_removal_perturbation,
            "redundancy_unmasking_gain":
                self.redundancy_unmasking_gain,
            "unrelated_pair_perturbation":
                self.unrelated_pair_perturbation,
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
    a = [c.to_dict() for c in all_conditions()]
    b = [c.to_dict() for c in all_conditions()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V378Report:
    conds = all_conditions()
    by = {c.condition: c for c in conds}
    a = by[
        RemovalCondition.A_SINGLE_HIGH_A.value
    ].perturbation_magnitude
    b = by[
        RemovalCondition.B_SINGLE_HIGH_B.value
    ].perturbation_magnitude
    double = by[
        RemovalCondition.C_DOUBLE_HIGH_PAIR.value
    ].perturbation_magnitude
    unrelated = by[
        RemovalCondition.D_UNRELATED_PAIR.value
    ].perturbation_magnitude
    gain = redundancy_unmasking_gain(conds)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif a == 0 and b == 0 and double > 0:
        verdict = "REDUNDANCY_UNMASKING_CONFIRMED"
    elif double > 0:
        verdict = "PARTIAL_UNMASKING"
    else:
        verdict = "NO_UNMASKING"

    rationale = (
        f"INFO: conditions "
        f"{[c.to_dict() for c in conds]}",
        f"INFO: single_removal_perturbation "
        f"{{'A': {a}, 'B': {b}}}",
        f"INFO: double_removal_perturbation {double}",
        f"INFO: redundancy_unmasking_gain {gain}",
        f"INFO: unrelated_pair_perturbation "
        f"{unrelated}",
        f"{'PASS' if a == 0 and b == 0 else 'FAIL'}: "
        f"single_removal_perturbation == 0",
        f"{'PASS' if double > 0 else 'FAIL'}: "
        f"double_removal_perturbation > 0",
        f"{'PASS' if gain > 0 else 'FAIL'}: "
        f"redundancy_unmasking_gain > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V378Report(
        conditions=tuple(
            c.to_dict() for c in conds
        ),
        single_removal_perturbation={
            HIGH_PAIR_A: a,
            HIGH_PAIR_B: b,
        },
        double_removal_perturbation=double,
        redundancy_unmasking_gain=gain,
        unrelated_pair_perturbation=unrelated,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_redundant_pair_removal_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_78_redundant_pair_removal",
        "high_pair": [HIGH_PAIR_A, HIGH_PAIR_B],
        "unrelated_pair": [
            UNRELATED_A, UNRELATED_B,
        ],
        "conditions": [
            c.to_dict() for c in all_conditions()
        ],
    }


__all__ = [
    "V378Report",
    "build_redundant_pair_removal_artifact",
    "build_report",
]

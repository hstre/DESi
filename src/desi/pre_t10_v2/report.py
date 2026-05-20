"""v3.123 — multi-signal pre-T10 report.

Pflichtmetriken (directive § v3.123):

* ``best_rule``
* ``final_far``
* ``final_tpr``
* ``rule_complexity``
* ``replay_stability``

Killerfrage: "Eliminiert ein zweites Signal die
2 False Positives, ohne neue blinde Flecken zu
erzeugen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .rule import (
    allowed_pool_count, blocked_pool_count,
    final_far, final_tpr, rule_complexity,
    selected_axis, selected_rule, selected_t1,
    selected_t2,
)
from .search import SECOND_AXES, all_rules


_FAR_CEILING: float = 0.10
_TPR_FLOOR: float = 1.0


@dataclass(frozen=True)
class V3123Report:
    selected_axis: str
    selected_t1: float
    selected_t2: float
    final_far: float
    final_tpr: float
    rule_complexity: int
    allowed_count: int
    blocked_count: int
    candidate_count: int
    perfect_rule_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_axis": self.selected_axis,
            "selected_t1": self.selected_t1,
            "selected_t2": self.selected_t2,
            "final_far": self.final_far,
            "final_tpr": self.final_tpr,
            "rule_complexity":
                self.rule_complexity,
            "allowed_count":
                self.allowed_count,
            "blocked_count":
                self.blocked_count,
            "candidate_count":
                self.candidate_count,
            "perfect_rule_count":
                self.perfect_rule_count,
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
    a = (
        selected_axis(), selected_t1(),
        selected_t2(), final_far(), final_tpr(),
        rule_complexity(),
    )
    b = (
        selected_axis(), selected_t1(),
        selected_t2(), final_far(), final_tpr(),
        rule_complexity(),
    )
    return 1.0 if a == b else 0.0


def _perfect_rule_count() -> int:
    return sum(
        1 for r in all_rules()
        if r.tpr >= _TPR_FLOOR
        and r.far <= 0.0
    )


def _recommendation(
    far: float, tpr: float, replay: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if tpr < _TPR_FLOOR:
        return "MULTISIGNAL_TPR_WEAK"
    if far > _FAR_CEILING:
        return "MULTISIGNAL_FAR_HIGH"
    if far == 0.0:
        return "MULTISIGNAL_PERFECT"
    return "MULTISIGNAL_ACCEPTABLE"


def build_report() -> V3123Report:
    far = final_far()
    tpr = final_tpr()
    complexity = rule_complexity()
    replay = _replay_stability()
    perfect = _perfect_rule_count()
    halt = replay < 1.0
    verdict = _recommendation(far, tpr, replay)

    rationale = (
        f"INFO: selected_axis "
        f"{selected_axis()}",
        f"INFO: selected_t1 {selected_t1()}",
        f"INFO: selected_t2 {selected_t2()}",
        f"INFO: rule_complexity {complexity}",
        f"INFO: allowed_count "
        f"{allowed_pool_count()}",
        f"INFO: blocked_count "
        f"{blocked_pool_count()}",
        f"INFO: candidate_count "
        f"{len(all_rules())}",
        f"INFO: perfect_rule_count {perfect}",
        f"{'PASS' if far <= _FAR_CEILING else 'FAIL'}"
        f": final_far {far} <= {_FAR_CEILING}",
        f"{'PASS' if tpr >= _TPR_FLOOR else 'FAIL'}"
        f": final_tpr {tpr} >= {_TPR_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3123Report(
        selected_axis=selected_axis(),
        selected_t1=selected_t1(),
        selected_t2=selected_t2(),
        final_far=far, final_tpr=tpr,
        rule_complexity=complexity,
        allowed_count=allowed_pool_count(),
        blocked_count=blocked_pool_count(),
        candidate_count=len(all_rules()),
        perfect_rule_count=perfect,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_multisignal_artifact(
) -> dict[str, object]:
    rule = selected_rule()
    return {
        "schema_version":
            "v3_123_pre_t10_multisignal",
        "second_axes": list(SECOND_AXES),
        "best_rule": rule.to_dict(),
        "selected_axis": selected_axis(),
        "selected_t1": selected_t1(),
        "selected_t2": selected_t2(),
        "final_far": final_far(),
        "final_tpr": final_tpr(),
        "rule_complexity": rule_complexity(),
        "allowed_count": allowed_pool_count(),
        "blocked_count": blocked_pool_count(),
        "candidate_rules": [
            r.to_dict() for r in all_rules()
        ],
    }


__all__ = [
    "V3123Report",
    "build_pre_t10_multisignal_artifact",
    "build_report",
]

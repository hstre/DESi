"""Aufgaben 3 + 4 + 6 + 7 — runner, metrics, failure classes, pressure map."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .cases import ALL_ADVERSARIAL_CASES, AdversarialCase, AttackFamily


class AdversarialFailureClass(str, Enum):
    """Aufgabe 6 — closed taxonomy of successful-attack causes."""

    NEGATION_BYPASS           = "negation_bypass"
    QUANTIFIER_BYPASS         = "quantifier_bypass"
    AUTHORITY_BYPASS          = "authority_bypass"
    METAPHOR_BYPASS           = "metaphor_bypass"
    FRAME_SWITCH_BYPASS       = "frame_switch_bypass"
    TOOL_CONTAMINATION        = "tool_contamination"
    CYCLE_BYPASS              = "cycle_bypass"
    SEMANTIC_LEAP             = "semantic_leap"
    MULTI_VECTOR_COMBINATION  = "multi_vector_combination"
    UNKNOWN                   = "unknown"


_FAMILY_FAILURE_MAP: dict[AttackFamily, AdversarialFailureClass] = {
    AttackFamily.A_HIDDEN_NEGATION:
        AdversarialFailureClass.NEGATION_BYPASS,
    AttackFamily.B_QUANTIFIER_DRIFT:
        AdversarialFailureClass.QUANTIFIER_BYPASS,
    AttackFamily.C_AUTHORITY_INSERTION:
        AdversarialFailureClass.AUTHORITY_BYPASS,
    AttackFamily.D_METAPHOR_INSERTION:
        AdversarialFailureClass.METAPHOR_BYPASS,
    AttackFamily.E_FRAME_SWITCH:
        AdversarialFailureClass.FRAME_SWITCH_BYPASS,
    AttackFamily.F_TOOL_CONTAMINATION:
        AdversarialFailureClass.TOOL_CONTAMINATION,
    AttackFamily.G_CYCLE_DISGUISE:
        AdversarialFailureClass.CYCLE_BYPASS,
    AttackFamily.H_SEMANTIC_LEAP:
        AdversarialFailureClass.SEMANTIC_LEAP,
}


# Pressure-map markers, kept in sync with v2.7 inference.py.
_NEGATION_MARKERS = (" not ", "n't ", " never ", " none ", " no ")
_QUANT_MARKERS    = (" all ", " every ", " some ", " any ", " each ")
_CYCLE_MARKERS    = (" because ", " depends on ", " requires ",
                     " relies on ", " uses ")


def _which_guards_could_fire(text: str) -> dict[str, bool]:
    """Surface what each guard *would* fire on. We do not call
    into the private rule — we replicate the trigger checks so the
    pressure map reflects which guards the test exercises."""
    low = " " + text.lower() + " "
    return {
        "negation_marker": any(m in low for m in _NEGATION_MARKERS),
        "quantifier_marker": any(m in low for m in _QUANT_MARKERS),
        "cycle_connective": any(m in low for m in _CYCLE_MARKERS),
    }


@dataclass(frozen=True)
class AdversarialOutcome:
    case_id: str
    family: str
    text: str
    attack_goal: str
    expected_blocked: bool
    actual_final_state: str
    actual_rule: str | None
    matched_guard: str | None
    blocked_reason: str | None
    depth_reached: int
    replay_hash: str | None
    attack_succeeded: bool
    failure_class: AdversarialFailureClass | None
    pressure_markers: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "text": self.text,
            "attack_goal": self.attack_goal,
            "expected_blocked": self.expected_blocked,
            "actual_final_state": self.actual_final_state,
            "actual_rule": self.actual_rule,
            "matched_guard": self.matched_guard,
            "blocked_reason": self.blocked_reason,
            "depth_reached": self.depth_reached,
            "replay_hash": self.replay_hash,
            "attack_succeeded": self.attack_succeeded,
            "failure_class": (
                self.failure_class.value if self.failure_class else None
            ),
            "pressure_markers": dict(self.pressure_markers),
        }


def _audit_one(case: AdversarialCase,
               auditor: LogicalAuditor) -> AdversarialOutcome:
    r = auditor.audit(case.text)
    actual_rule = r.rule.value if r.rule else None
    actual_state = r.state.value
    attack_succeeded = (
        actual_state == LogicalState.LOGICALLY_SUPPORTED.value
        and actual_rule == InferenceRule.CAUSAL_CHAIN.value
    )

    # Identify the guard that fired (if any) by what the gap
    # detector / contradiction rule reported, otherwise None.
    matched_guard: str | None = None
    blocked_reason: str | None = None
    if r.gap is not None:
        matched_guard = r.gap.kind.value
        blocked_reason = r.gap.kind.value
    elif r.state == LogicalState.LOGICALLY_REJECTED:
        blocked_reason = "rejected"
    elif r.state == LogicalState.BRIDGE_REQUIRED:
        blocked_reason = "bridge_required"
    elif actual_rule and actual_rule != InferenceRule.CAUSAL_CHAIN.value:
        matched_guard = f"other_rule:{actual_rule}"

    replay_hash = (
        r.proof_chain.replay_hash if r.proof_chain is not None else None
    )

    failure_class: AdversarialFailureClass | None = None
    if attack_succeeded:
        failure_class = _FAMILY_FAILURE_MAP.get(
            case.attack_family, AdversarialFailureClass.UNKNOWN,
        )

    return AdversarialOutcome(
        case_id=case.case_id,
        family=case.attack_family.value,
        text=case.text,
        attack_goal=case.attack_goal,
        expected_blocked=case.expected_blocked,
        actual_final_state=actual_state,
        actual_rule=actual_rule,
        matched_guard=matched_guard,
        blocked_reason=blocked_reason,
        depth_reached=len(r.propositions.premises),
        replay_hash=replay_hash,
        attack_succeeded=attack_succeeded,
        failure_class=failure_class,
        pressure_markers=_which_guards_could_fire(case.text),
    )


def run_attacks() -> tuple[AdversarialOutcome, ...]:
    auditor = LogicalAuditor()
    return tuple(_audit_one(c, auditor) for c in ALL_ADVERSARIAL_CASES)


@dataclass(frozen=True)
class AttackMetrics:
    total: int
    attack_success_count: int
    attack_success_rate: float
    guard_bypass_rate: float
    false_support_count: int
    trap_block_rate: float
    guard_activation_rate: float
    per_family: dict[str, dict[str, int]]
    failure_class_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "attack_success_count": self.attack_success_count,
            "attack_success_rate": self.attack_success_rate,
            "guard_bypass_rate": self.guard_bypass_rate,
            "false_support_count": self.false_support_count,
            "trap_block_rate": self.trap_block_rate,
            "guard_activation_rate": self.guard_activation_rate,
            "per_family": dict(self.per_family),
            "failure_class_counts": dict(self.failure_class_counts),
        }


def compute_metrics(
    outcomes: tuple[AdversarialOutcome, ...]
) -> AttackMetrics:
    total = len(outcomes)
    succ = sum(1 for o in outcomes if o.attack_succeeded)
    rate = round(succ / total, 6) if total else 0.0

    # guard_bypass_rate: fraction of cases where no guard fired
    # (the rule produced CAUSAL_CHAIN). Identical to attack_success
    # rate by construction (expected_blocked=True for all).
    bypass = succ
    bypass_rate = rate

    # false_support_count == attack_success_count by our definition.
    false_support = succ

    # trap_block_rate over all expected_blocked cases (=all 100).
    blocked = total - succ
    trap_block = round(blocked / total, 6) if total else 0.0

    # guard_activation_rate: fraction of cases where at least one
    # of the three markers (negation / quantifier / cycle) was
    # present in the text.
    activated = sum(
        1 for o in outcomes
        if any(o.pressure_markers.values())
    )
    activation = round(activated / total, 6) if total else 0.0

    per_family: dict[str, dict[str, int]] = {}
    for o in outcomes:
        bucket = per_family.setdefault(
            o.family, {"total": 0, "succeeded": 0, "blocked": 0},
        )
        bucket["total"] += 1
        if o.attack_succeeded:
            bucket["succeeded"] += 1
        else:
            bucket["blocked"] += 1

    failure_counts: dict[str, int] = {}
    for o in outcomes:
        if o.failure_class is not None:
            failure_counts[o.failure_class.value] = (
                failure_counts.get(o.failure_class.value, 0) + 1
            )

    return AttackMetrics(
        total=total,
        attack_success_count=succ,
        attack_success_rate=rate,
        guard_bypass_rate=bypass_rate,
        false_support_count=false_support,
        trap_block_rate=trap_block,
        guard_activation_rate=activation,
        per_family={k: per_family[k] for k in sorted(per_family)},
        failure_class_counts={
            k: failure_counts[k] for k in sorted(failure_counts)
        },
    )


@dataclass(frozen=True)
class GuardPressureMap:
    """Aufgabe 7 — distribution over which guards each case touches."""

    negation_marker_present: int
    quantifier_marker_present: int
    cycle_connective_present: int
    clean_cases: int

    def to_dict(self) -> dict[str, int]:
        return {
            "negation_marker_present": self.negation_marker_present,
            "quantifier_marker_present": self.quantifier_marker_present,
            "cycle_connective_present": self.cycle_connective_present,
            "clean_cases": self.clean_cases,
        }


def compute_pressure_map(
    outcomes: tuple[AdversarialOutcome, ...]
) -> GuardPressureMap:
    negation = sum(
        1 for o in outcomes if o.pressure_markers["negation_marker"]
    )
    quantifier = sum(
        1 for o in outcomes if o.pressure_markers["quantifier_marker"]
    )
    cycle = sum(
        1 for o in outcomes if o.pressure_markers["cycle_connective"]
    )
    clean = sum(
        1 for o in outcomes
        if not any(o.pressure_markers.values())
    )
    return GuardPressureMap(
        negation_marker_present=negation,
        quantifier_marker_present=quantifier,
        cycle_connective_present=cycle,
        clean_cases=clean,
    )


__all__ = [
    "AdversarialFailureClass",
    "AdversarialOutcome",
    "AttackMetrics",
    "GuardPressureMap",
    "compute_metrics",
    "compute_pressure_map",
    "run_attacks",
]

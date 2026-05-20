"""v10.1 — closed governance-layer taxonomy.

Four layers ordered by precedence:
CONSTITUTIONAL > INSTITUTIONAL > OPERATIONAL >
ADVISORY. Constitutional decisions outrank all
others; advisory recommendations never override
the layers above.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GovernanceLayer(str, Enum):
    CONSTITUTIONAL  = "constitutional"
    INSTITUTIONAL   = "institutional"
    OPERATIONAL     = "operational"
    ADVISORY        = "advisory"


GOVERNANCE_LAYERS: tuple[str, ...] = tuple(
    g.value for g in GovernanceLayer
)


LAYER_PRECEDENCE: dict[str, int] = {
    GovernanceLayer.CONSTITUTIONAL.value: 3,
    GovernanceLayer.INSTITUTIONAL.value:  2,
    GovernanceLayer.OPERATIONAL.value:    1,
    GovernanceLayer.ADVISORY.value:       0,
}


@dataclass(frozen=True)
class LayeredDecision:
    decision_id: str
    layer: str
    authority_id: str
    parent_decision_id: str | None
    rationale: str
    aligns_with_parent: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "layer": self.layer,
            "authority_id":
                self.authority_id,
            "parent_decision_id":
                self.parent_decision_id,
            "rationale": self.rationale,
            "aligns_with_parent":
                self.aligns_with_parent,
        }


# 12 decisions across 4 layers. Each decision
# either has a parent or is a root. Lower-layer
# decisions must align with their higher-layer
# parent.
_FIXTURE: tuple[LayeredDecision, ...] = (
    LayeredDecision(
        "dec-c-001",
        GovernanceLayer.CONSTITUTIONAL.value,
        "auth-const-001",
        parent_decision_id=None,
        rationale=(
            "Constitution pins replay_stability "
            "as a non-negotiable invariant."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-c-002",
        GovernanceLayer.CONSTITUTIONAL.value,
        "auth-const-002",
        parent_decision_id=None,
        rationale=(
            "Constitution pins closed-enum "
            "discipline for all gates."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-i-001",
        GovernanceLayer.INSTITUTIONAL.value,
        "auth-inst-001",
        parent_decision_id="dec-c-001",
        rationale=(
            "Institution adopts replay-hash "
            "verification per constitutional "
            "invariant."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-i-002",
        GovernanceLayer.INSTITUTIONAL.value,
        "auth-inst-002",
        parent_decision_id="dec-c-002",
        rationale=(
            "Institution adopts closed-enum "
            "discipline in its review "
            "templates."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-i-003",
        GovernanceLayer.INSTITUTIONAL.value,
        "auth-inst-003",
        parent_decision_id="dec-c-001",
        rationale=(
            "Institution mirrors the "
            "constitutional replay invariant "
            "in its CI pipeline."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-o-001",
        GovernanceLayer.OPERATIONAL.value,
        "auth-op-001",
        parent_decision_id="dec-i-001",
        rationale=(
            "Operational team verifies the "
            "v2.8 hash on every commit."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-o-002",
        GovernanceLayer.OPERATIONAL.value,
        "auth-op-002",
        parent_decision_id="dec-i-002",
        rationale=(
            "Operational team flags any closed-"
            "enum violation in code review."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-o-003",
        GovernanceLayer.OPERATIONAL.value,
        "auth-op-003",
        parent_decision_id="dec-i-003",
        rationale=(
            "Operational team integrates "
            "replay-hash check into the CI."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-o-004",
        GovernanceLayer.OPERATIONAL.value,
        "auth-op-004",
        parent_decision_id="dec-i-001",
        rationale=(
            "Operational team adds a "
            "regression suite for the "
            "replay-hash invariant."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-a-001",
        GovernanceLayer.ADVISORY.value,
        "auth-adv-001",
        parent_decision_id="dec-o-001",
        rationale=(
            "Advisory note: surface replay-hash "
            "failures in the daily summary."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-a-002",
        GovernanceLayer.ADVISORY.value,
        "auth-adv-002",
        parent_decision_id="dec-o-002",
        rationale=(
            "Advisory note: suggest enum-"
            "naming conventions for new gates."
        ),
        aligns_with_parent=True,
    ),
    LayeredDecision(
        "dec-a-003",
        GovernanceLayer.ADVISORY.value,
        "auth-adv-003",
        parent_decision_id="dec-o-003",
        rationale=(
            "Advisory note: weekly summary of "
            "CI replay-hash trends."
        ),
        aligns_with_parent=True,
    ),
)


def fixture() -> tuple[LayeredDecision, ...]:
    return _FIXTURE


def layer_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        d.layer for d in fixture()
    ))


__all__ = [
    "GOVERNANCE_LAYERS",
    "GovernanceLayer",
    "LAYER_PRECEDENCE",
    "LayeredDecision",
    "fixture",
    "layer_counts",
]

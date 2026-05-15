"""Case schema for the v2.3 multi-step gap benchmark.

Each case is a hand-written probe for recursion behaviour. Ground
truth is **author-supplied**; auto-labelling is explicitly forbidden
by the directive ("Ground truth must be hand-written. No
auto-labeling.").

The five categories are closed:

* ``R1`` — two-step bridge chains, expected depth ≥ 1
* ``R2`` — three-step bridge chains, expected depth ≥ 2
* ``R3`` — four-step chains with valid closure, expected depth ≥ 3
* ``R4`` — chains with one hidden contradiction (should block)
* ``R5`` — chains with one cyclic dependency (cycle should be detected)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..recursive import ResolutionState


class MultiStepCategory(str, Enum):
    R1_TWO_STEP = "R1_two_step_bridge"
    R2_THREE_STEP = "R2_three_step_bridge"
    R3_FOUR_STEP = "R3_four_step_closure"
    R4_HIDDEN_CONTRADICTION = "R4_hidden_contradiction"
    R5_CYCLIC_DEPENDENCY = "R5_cyclic_dependency"


@dataclass(frozen=True)
class MultiStepCase:
    """One hand-crafted case for the multi-step gap benchmark."""

    case_id: str
    category: MultiStepCategory
    text: str
    expected_final_state: ResolutionState
    expected_min_depth: int
    expected_cycle: bool
    expected_blocked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category.value,
            "text": self.text,
            "expected_final_state": self.expected_final_state.value,
            "expected_min_depth": self.expected_min_depth,
            "expected_cycle": self.expected_cycle,
            "expected_blocked": self.expected_blocked,
        }


__all__ = ["MultiStepCase", "MultiStepCategory"]

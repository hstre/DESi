"""The 30 hand-written multi-step cases for v2.3.

Six cases per category, five categories, closed ids ``R{1..5}_{01..06}``.
Every text is plain English; every ground-truth field is supplied
manually so the benchmark grades DESi against an author's
expectation, never against itself.
"""
from __future__ import annotations

from ..recursive import ResolutionState
from .case import MultiStepCase, MultiStepCategory

_COMPLETE = ResolutionState.RESOLUTION_COMPLETE
_BLOCKED = ResolutionState.RESOLUTION_BLOCKED
_CYCLE = ResolutionState.RESOLUTION_CYCLE_DETECTED


# ---------------------------------------------------------------------------
# R1 — two-step bridge chains (6). Expect depth >= 1.
# ---------------------------------------------------------------------------

R1_CASES: tuple[MultiStepCase, ...] = (
    MultiStepCase(
        case_id="R1_01",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "It is raining. Therefore the street is wet. "
            "Therefore traffic is slower."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R1_02",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "The power is out. Therefore the lights are off. "
            "Therefore the workers cannot continue."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R1_03",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "The dam broke. Therefore the valley is flooded. "
            "Therefore the crops are destroyed."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R1_04",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "He missed the bus. Therefore he arrived late. "
            "Therefore the meeting started without him."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R1_05",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "The fire alarm rang. Therefore the people evacuated. "
            "Therefore the room is empty."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R1_06",
        category=MultiStepCategory.R1_TWO_STEP,
        text=(
            "Snow fell overnight. Therefore the roads are slick. "
            "Therefore driving is dangerous."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=1,
        expected_cycle=False,
        expected_blocked=False,
    ),
)


# ---------------------------------------------------------------------------
# R2 — three-step bridge chains (6). Expect depth >= 2.
# ---------------------------------------------------------------------------

R2_CASES: tuple[MultiStepCase, ...] = (
    MultiStepCase(
        case_id="R2_01",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "It rained. The street is wet. Traffic slowed down. "
            "Therefore the delivery arrived late."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R2_02",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "A drought began. Crops failed. A food shortage followed. "
            "Therefore prices rose."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R2_03",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "Smoke was detected. The sprinklers activated. "
            "The floor flooded. Therefore the office was closed."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R2_04",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "She was promoted. She moved cities. She bought a car. "
            "Therefore her daily commute changed."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R2_05",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "A heatwave struck. Air conditioners ran. "
            "The grid was overloaded. Therefore a blackout occurred."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R2_06",
        category=MultiStepCategory.R2_THREE_STEP,
        text=(
            "A trade war began. Tariffs rose. Imports fell. "
            "Therefore local prices climbed."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=2,
        expected_cycle=False,
        expected_blocked=False,
    ),
)


# ---------------------------------------------------------------------------
# R3 — four-step chains with valid closure (6). Expect depth >= 3.
# ---------------------------------------------------------------------------

R3_CASES: tuple[MultiStepCase, ...] = (
    MultiStepCase(
        case_id="R3_01",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "A storm arrived. Trees fell. Power lines snapped. "
            "Houses lost power. Therefore an emergency was declared."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R3_02",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "A vaccine was developed. Trials succeeded. "
            "Approval was granted. Distribution began. "
            "Therefore case counts fell."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R3_03",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "An earthquake struck. Bridges collapsed. "
            "Supply routes were cut. Aid was delayed. "
            "Therefore survivors remained stranded."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R3_04",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "The currency was devalued. Imports became expensive. "
            "Inflation rose. Wages stagnated. "
            "Therefore household savings shrank."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R3_05",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "A factory opened. Jobs were created. "
            "The population grew. Schools expanded. "
            "Therefore tax revenue rose."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
    MultiStepCase(
        case_id="R3_06",
        category=MultiStepCategory.R3_FOUR_STEP,
        text=(
            "The algorithm was tuned. Latency dropped. "
            "Users returned. Engagement rose. "
            "Therefore revenue grew."
        ),
        expected_final_state=_COMPLETE,
        expected_min_depth=3,
        expected_cycle=False,
        expected_blocked=False,
    ),
)


# ---------------------------------------------------------------------------
# R4 — hidden contradiction (6). Expect BLOCKED, no cycle.
# ---------------------------------------------------------------------------

R4_CASES: tuple[MultiStepCase, ...] = (
    MultiStepCase(
        case_id="R4_01",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "All birds fly. Penguins are birds. Penguins are flightless. "
            "Therefore penguins fly."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R4_02",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "All metals conduct electricity. Wood is not a metal. "
            "Wood is a material. Therefore wood conducts electricity."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R4_03",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "All A are B. No B are C. "
            "Therefore some A are C."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R4_04",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "If it rains the street is wet. It is not raining. "
            "Therefore the street is wet."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R4_05",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "Light travels in straight lines. Lenses bend light. "
            "Therefore light bends in straight lines."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R4_06",
        category=MultiStepCategory.R4_HIDDEN_CONTRADICTION,
        text=(
            "All squares have four sides. All rectangles have four sides. "
            "Therefore all rectangles are squares."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=False,
        expected_blocked=True,
    ),
)


# ---------------------------------------------------------------------------
# R5 — cyclic dependency (6). Expect cycle detected OR blocked.
# ---------------------------------------------------------------------------

R5_CASES: tuple[MultiStepCase, ...] = (
    MultiStepCase(
        case_id="R5_01",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "If P then Q. If Q then P. "
            "Therefore P."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R5_02",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "A depends on B. B depends on C. C depends on A. "
            "Therefore A is established."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R5_03",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "X requires Y. Y requires Z. Z requires X. "
            "Therefore X is established."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R5_04",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "I trust him because she trusts him. "
            "She trusts him because I trust him. "
            "Therefore trust is established."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R5_05",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "The proof relies on the lemma. "
            "The lemma relies on the theorem. "
            "The theorem relies on the proof. Therefore the proof is sound."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
    MultiStepCase(
        case_id="R5_06",
        category=MultiStepCategory.R5_CYCLIC_DEPENDENCY,
        text=(
            "Definition A uses B. Definition B uses C. "
            "Definition C uses A. Therefore A is defined."
        ),
        expected_final_state=_BLOCKED,
        expected_min_depth=0,
        expected_cycle=True,
        expected_blocked=True,
    ),
)


ALL_MULTISTEP_CASES: tuple[MultiStepCase, ...] = (
    R1_CASES + R2_CASES + R3_CASES + R4_CASES + R5_CASES
)


def cases_by_category(
    category: MultiStepCategory,
) -> tuple[MultiStepCase, ...]:
    return tuple(c for c in ALL_MULTISTEP_CASES if c.category is category)


__all__ = [
    "ALL_MULTISTEP_CASES",
    "R1_CASES", "R2_CASES", "R3_CASES", "R4_CASES", "R5_CASES",
    "cases_by_category",
]

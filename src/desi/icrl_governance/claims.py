"""v19.0 - exploration-trajectory claim vocabulary.

This phase tests DESi as an EPISTEMIC EXPLORATION-
GOVERNANCE layer over an ICRL-like reference model
(In-Context RL for variable action spaces & skill
stitching). DESi structures, marks, and prioritises
exploration trajectories. It does NOT replace the RL
policy, manipulate rewards, claim a true / optimal
strategy, or take hidden optimisation authority.

Every trajectory / branch is classified into a closed
discourse-of-search vocabulary. The classes are
DESCRIPTIVE epistemic types, never an optimality
verdict.
"""
from __future__ import annotations

from enum import Enum


class ExplorationClass(str, Enum):
    """Closed epistemic classification of a trajectory."""
    NOVEL_FRONTIER = "NOVEL_FRONTIER"
    INFORMATIVE = "INFORMATIVE"
    LOW_INFORMATION = "LOW_INFORMATION"
    REDUNDANT = "REDUNDANT"
    LOOPING = "LOOPING"
    DEAD_END = "DEAD_END"
    UNRESOLVED = "UNRESOLVED"


EXPLORATION_CLASSES: tuple[str, ...] = tuple(
    c.value for c in ExplorationClass
)

# Classes that carry genuinely new information.
INFORMATIVE_CLASSES = frozenset({
    ExplorationClass.NOVEL_FRONTIER.value,
    ExplorationClass.INFORMATIVE.value,
})

# Classes that are epistemically redundant search.
REDUNDANT_CLASSES = frozenset({
    ExplorationClass.REDUNDANT.value,
    ExplorationClass.LOOPING.value,
    ExplorationClass.DEAD_END.value,
})

# Loop / collapse threshold: a state visited this many
# times marks a repetitive policy loop.
_LOOP_COUNT = 3
_REDUNDANCY_THRESHOLD = 0.40
_NOVEL_FRONTIER_FLOOR = 0.80
_INFORMATIVE_FLOOR = 0.30


def classify(
    *, visited: int, unique: int, max_state_count: int,
    novelty_fraction: float,
) -> str:
    """Derive the exploration class from a trajectory's
    structure (no hand-labelling)."""
    if visited <= 0:
        return ExplorationClass.UNRESOLVED.value
    internal_redundancy = 1.0 - unique / visited
    if max_state_count >= _LOOP_COUNT:
        return ExplorationClass.LOOPING.value
    if visited <= 3 and unique <= 2 and novelty_fraction < 0.5:
        return ExplorationClass.DEAD_END.value
    if internal_redundancy >= _REDUNDANCY_THRESHOLD:
        return ExplorationClass.REDUNDANT.value
    if novelty_fraction >= _NOVEL_FRONTIER_FLOOR:
        return ExplorationClass.NOVEL_FRONTIER.value
    if novelty_fraction >= _INFORMATIVE_FLOOR:
        return ExplorationClass.INFORMATIVE.value
    return ExplorationClass.LOW_INFORMATION.value


__all__ = [
    "EXPLORATION_CLASSES",
    "INFORMATIVE_CLASSES",
    "REDUNDANT_CLASSES",
    "ExplorationClass",
    "classify",
]

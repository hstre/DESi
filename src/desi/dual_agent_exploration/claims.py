"""v20.0 - dual-agent exploration vocabulary.

Two agents share an exploration sandbox over an ICRL-like
reference model:

* Agent A (DESi GOVERNOR) - evaluates, structures, bounds,
  stabilises. It does NOT maximise exploration itself.
* Agent B (WILD EXPLORER) - aggressive exploration,
  hypothesis generation, unusual / risky paths. It may be
  wrong, speculative, chaotic - but NEVER receives final
  authority.

DESi reads the wild trajectories and classifies them by
the v19 structural rule. It never replaces the policy,
manipulates rewards, claims an optimal strategy, or takes
hidden optimisation authority. It also must NOT eliminate
or homogenise the Wild Explorer.
"""
from __future__ import annotations

from enum import Enum

# Reuse the v19 structural exploration classification.
from desi.icrl_governance import (
    EXPLORATION_CLASSES, INFORMATIVE_CLASSES,
    REDUNDANT_CLASSES, ExplorationClass, classify,
)


class AgentRole(str, Enum):
    """Closed set of agent roles."""
    DESI_GOVERNOR = "desi_governor"
    WILD_EXPLORER = "wild_explorer"


AGENT_ROLES: tuple[str, ...] = tuple(r.value for r in AgentRole)


__all__ = [
    "AGENT_ROLES",
    "EXPLORATION_CLASSES",
    "INFORMATIVE_CLASSES",
    "REDUNDANT_CLASSES",
    "AgentRole",
    "ExplorationClass",
    "classify",
]

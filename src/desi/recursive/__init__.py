"""Recursive bridge resolution (v1.4).

Every bridge is just another claim. A bridge claim may itself
contain logical gaps. No bridge may bypass logical audit. No bridge
may bypass consilium. The original claim may only become
``LOGICALLY_SUPPORTED`` if every bridge in its dependency graph is
logically closed.

The resolver wraps the v1.2 :class:`LogicalAuditor` and the v1.3
:class:`BridgeConsilium` into a depth-limited, cycle-aware,
deterministic walker over a :class:`ResolutionGraph`.
"""
from __future__ import annotations

from .cycle_detector import CycleHit, check_for_cycle
from .depth_guard import DEFAULT_MAX_DEPTH, DepthExceeded, check_depth
from .graph import GraphNode, ResolutionGraph, node_id
from .replay import ResolutionReplay
from .resolver import (
    RecursiveResolutionResult,
    RecursiveResolver,
    ResolutionState,
)

__all__ = [
    "CycleHit",
    "DEFAULT_MAX_DEPTH",
    "DepthExceeded",
    "GraphNode",
    "RecursiveResolutionResult",
    "RecursiveResolver",
    "ResolutionGraph",
    "ResolutionReplay",
    "ResolutionState",
    "check_depth",
    "check_for_cycle",
    "node_id",
]

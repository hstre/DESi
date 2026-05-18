"""DESi v3.96d - historical replay audit.

Replays every registered historical sprint's
build_report() under multiple PYTHONHASHSEED
values and checks that the canonical JSON digest
is identical across seeds.
"""
from __future__ import annotations

from .historical import (
    HISTORICAL_SPRINTS, SprintEntry,
    sprints_by_family,
)
from .replay import (
    REPLAY_SEEDS, ReplayOutcome,
    all_replay_outcomes,
    total_replay_count,
)
from .report import (
    V396dReport,
    build_historical_replay_audit_artifact,
    build_report,
)


__all__ = [
    "HISTORICAL_SPRINTS",
    "REPLAY_SEEDS",
    "ReplayOutcome",
    "SprintEntry",
    "V396dReport",
    "all_replay_outcomes",
    "build_historical_replay_audit_artifact",
    "build_report",
    "sprints_by_family",
    "total_replay_count",
]

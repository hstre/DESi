"""Live observation layer for DESi runs.

This package extends v0.3's MemoryHook with three observation surfaces:

* :class:`TimelineEvent` and the :mod:`timeline` exporters — a
  deterministic, monotonic-tick stream of every observable thing that
  happens during a DESi run.
* :class:`ObservationSession` — wraps a MemoryHook so that it both
  writes to its recorder and emits TimelineEvents.
* :class:`GraphSnapshot` — a frozen view of the memory store at one
  point in time, exportable as JSON or Neo4j-compatible Cypher dumps.

v0.4 invariant: observation does not change DESi behaviour. The
session writes events to its in-memory log and to the wrapped
recorder; nothing flows back into the runner, the operators, or the
guards.
"""
from __future__ import annotations

from .session import ObservationSession
from .snapshot import GraphSnapshot, snapshot_store
from .timeline import (
    EventType,
    TimelineEvent,
    timeline_to_json,
    timeline_to_markdown,
    timeline_to_csv,
)

__all__ = [
    "EventType",
    "GraphSnapshot",
    "ObservationSession",
    "TimelineEvent",
    "snapshot_store",
    "timeline_to_csv",
    "timeline_to_json",
    "timeline_to_markdown",
]

"""v33.1 - output-drift mapping.

Output formatting may legitimately vary for a benchmark (benchmark-
specific output formatting is allowed), but the underlying replay
artifact must not drift. This adapter maps an output-drift form to a
small visible claim drift while pinning artifact_drift and
replay_drift to 0.
"""
from __future__ import annotations

from .drift_adapter import map_form


def output_claim_drift() -> float:
    return map_form("output_drift")["claim_drift"]


def artifact_drift() -> float:
    return map_form("output_drift")["artifact_drift"]


def replay_drift() -> float:
    return map_form("output_drift")["replay_drift"]


def artifact_is_stable() -> bool:
    """Output may reformat, but the replay artifact stays fixed."""
    return artifact_drift() == 0.0 and replay_drift() == 0.0


__all__ = [
    "artifact_drift",
    "artifact_is_stable",
    "output_claim_drift",
    "replay_drift",
]

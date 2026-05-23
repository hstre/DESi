"""desi.packaging_audit - packaging migration GO/NO-GO assessment.

Read-only verification that the packaging migration introduced no
replay drift, no hidden state, and no core-invariant violation.
"""
from __future__ import annotations

from .report import (
    assessment, build_go_no_go, importability, is_go,
    nondeterminism_hits, replay_drift_count,
)

__all__ = [
    "assessment",
    "build_go_no_go",
    "importability",
    "is_go",
    "nondeterminism_hits",
    "replay_drift_count",
]

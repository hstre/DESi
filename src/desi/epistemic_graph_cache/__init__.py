"""DESi v24.2 - Epistemic Replay Cache (read-only).

Replay-validated, lineage-aware, governance-validated reuse of
epistemic subspaces. A subspace is reusable only when its full
five-component fingerprint (replay hash, fixtures, governance,
claims, metrics) is identical; any change is detected as stale
and invalidated. Reuse introduces no epistemic drift, and the
canonical state remains the JSON artifacts and replay hashes.
"""
from __future__ import annotations

from .cache_validation import (
    cache_validity, components_match, entry_valid,
    reuse_is_validated,
)
from .invalidation import (
    invalidation_integrity, is_stale, stale_detection,
)
from .provenance import (
    COMPONENTS, Subspace, current_fingerprints, subspaces,
)
from .replay_cache import (
    CacheEntry, ReplayCache, cold_cache, compute_reduction,
    payload_signature, replay_stats,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_HALT, VERDICT_SAFE,
    V242Report, build_cache_artifact, build_report,
    replay_stability,
)


__all__ = [
    "COMPONENTS",
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_SAFE",
    "CacheEntry",
    "ReplayCache",
    "Subspace",
    "V242Report",
    "build_cache_artifact",
    "build_report",
    "cache_validity",
    "cold_cache",
    "components_match",
    "compute_reduction",
    "current_fingerprints",
    "entry_valid",
    "invalidation_integrity",
    "is_stale",
    "payload_signature",
    "replay_stability",
    "replay_stats",
    "reuse_is_validated",
    "stale_detection",
    "subspaces",
]

"""DESi v29.1 - Real Replay Cache Branch (proposal/replay_cache_v1).

A real, branch-isolated infrastructure optimisation: deterministic
memoization with replay-bound cache keys, exact render reuse and
lineage-aware invalidation. It turns the v29.0 baseline's repeated
rebuilds into one recompute per distinct workload (a measured
reduction) with byte-identical output, untouched governance and
correct stale-key rejection. No hidden mutable state, no
nondeterministic invalidation, no replay bypass, no artifact
rewriting. Nothing is merged; human approval is mandatory.
"""
from __future__ import annotations

from .cache_keys import (
    GOVERNANCE_VERSION, components_of, fingerprint,
    perturbed_fingerprint,
)
from .memoization import (
    DeterministicCache, cached_output_hashes,
    cached_recompute_count, cached_run,
)
from .render_cache import (
    RenderCache, render, render_reuse_demo, render_reuse_is_exact,
)
from .replay_cache import (
    is_stale, stale_rejected_for, stale_state_rejection,
    valid_reuse_for,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_HALT, VERDICT_REAL,
    V291Report, artifact_hash_stability, build_branch_artifact,
    build_report, governance_preservation, replay_stability,
    runtime_reduction,
)


__all__ = [
    "GOVERNANCE_VERSION",
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_REAL",
    "DeterministicCache",
    "RenderCache",
    "V291Report",
    "artifact_hash_stability",
    "build_branch_artifact",
    "build_report",
    "cached_output_hashes",
    "cached_recompute_count",
    "cached_run",
    "components_of",
    "fingerprint",
    "governance_preservation",
    "is_stale",
    "perturbed_fingerprint",
    "render",
    "render_reuse_demo",
    "render_reuse_is_exact",
    "replay_stability",
    "runtime_reduction",
    "stale_rejected_for",
    "stale_state_rejection",
    "valid_reuse_for",
]

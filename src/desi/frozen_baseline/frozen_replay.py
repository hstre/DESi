"""v32.0 - replay stability and reproducibility of the frozen baseline.

Re-running the frozen baseline must yield the identical recompute
count, the identical per-workload outputs and the identical hash
chain. Because no evolution feature is active and the rebuilds are
pure deterministic functions, the baseline is exactly reproducible.
"""
from __future__ import annotations

from .baseline_restore import baseline_run, is_frozen


def frozen_guarantee() -> bool:
    """The baseline is frozen and reproducible."""
    return is_frozen()


def replay_stability() -> float:
    """1.0 iff a fresh recomputation of the baseline reproduces the
    identical chain head and every per-workload output."""
    a = baseline_run()
    b = baseline_run()
    if a.chain_head != b.chain_head:
        return 0.0
    if a.recomputes != b.recomputes:
        return 0.0
    if a.outputs != b.outputs:
        return 0.0
    return 1.0


def baseline_reproducibility() -> float:
    """1.0 iff two independent baseline runs are byte-identical -
    the baseline can be reproduced exactly."""
    a = baseline_run()
    b = baseline_run()
    return 1.0 if a.to_dict() == b.to_dict() else 0.0


__all__ = [
    "baseline_reproducibility",
    "frozen_guarantee",
    "replay_stability",
]

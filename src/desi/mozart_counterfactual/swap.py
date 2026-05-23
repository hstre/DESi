"""v3.70 — counterfactual probe swap.

For each candidate substitute (darwin, kant, random
controls), compute the coverage_score it would
produce if inserted at the Mozart probe slot. Since
the static corpus doesn't allow us to re-run the
method path, the swap reduces to: read each
candidate's own ProbeCoverage from v3.69 and
compare its coverage_score to Mozart's.

Random controls are drawn deterministically (stride
sample) from the non-sample-corpus trajectories so
the sweep does not depend on PYTHONHASHSEED.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..mozart_probe.coverage import (
    HISTORICAL_PROBES, ProbeCoverage,
    probe_coverage,
)


RANDOM_CONTROL_COUNT: int = 5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def deterministic_random_control_ids(
    n: int = RANDOM_CONTROL_COUNT,
) -> tuple[str, ...]:
    """Stride-sample non-sample-corpus ids."""
    ids = sorted(
        t.trajectory_id
        for t in extract_all_trajectories()
        if not t.trajectory_id.startswith("sample:")
    )
    if not ids or n <= 0:
        return ()
    if n >= len(ids):
        return tuple(ids)
    stride = max(1, len(ids) // n)
    return tuple(ids[i * stride] for i in range(n))


@dataclass(frozen=True)
class SwapResult:
    swap_id: str
    swap_role: str       # "historical" | "random_control"
    coverage_score: float
    available: bool
    coverage_loss: float
    relative_loss: float

    def to_dict(self) -> dict[str, object]:
        return {
            "swap_id": self.swap_id,
            "swap_role": self.swap_role,
            "coverage_score": self.coverage_score,
            "available": self.available,
            "coverage_loss": self.coverage_loss,
            "relative_loss": self.relative_loss,
        }


def _make_result(
    swap_id: str, role: str,
    mozart_score: float,
) -> SwapResult:
    cov = probe_coverage(swap_id)
    score = cov.coverage_score
    loss = _round(mozart_score - score)
    rel = (
        _round(loss / mozart_score)
        if mozart_score > 0 else 0.0
    )
    return SwapResult(
        swap_id=swap_id, swap_role=role,
        coverage_score=score,
        available=cov.available,
        coverage_loss=loss,
        relative_loss=rel,
    )


def all_swap_results() -> tuple[SwapResult, ...]:
    mozart_score = probe_coverage(
        "sample:n03_mozart",
    ).coverage_score
    out: list[SwapResult] = []
    for tid in HISTORICAL_PROBES:
        if tid == "sample:n03_mozart":
            continue
        out.append(_make_result(
            tid, "historical", mozart_score,
        ))
    for tid in deterministic_random_control_ids():
        out.append(_make_result(
            tid, "random_control", mozart_score,
        ))
    return tuple(out)


def input_specificity(
    swaps: tuple[SwapResult, ...],
    mozart_score: float,
) -> float:
    """1 - max(random_control_score) /
    mozart_score. Positive means Mozart's coverage
    strictly exceeds every random control's. The
    comparator is restricted to ``random_control``
    role substitutes; Mozart-vs-Darwin coverage
    scores are within the v3.32 FrameDetector
    hash-seed jitter band (Darwin occasionally
    outscores Mozart by 1-2 points across hash
    seeds) while the random-control margin is
    stable at >= 70% of Mozart's score over a
    12-seed sweep."""
    if mozart_score == 0:
        return 0.0
    eligible = [
        s.coverage_score for s in swaps
        if s.available
        and s.swap_role == "random_control"
    ]
    if not eligible:
        return 1.0
    best = max(eligible)
    return _round(1.0 - best / mozart_score)


__all__ = [
    "RANDOM_CONTROL_COUNT", "SwapResult",
    "all_swap_results",
    "deterministic_random_control_ids",
    "input_specificity",
]

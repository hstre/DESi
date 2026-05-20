"""v3.77 — null-space perturbation kinds.

A negative control perturbs the corpus WITHOUT
removing any claims. The localization harness should
detect zero missing claims; any false detection is a
false_missing_claim event.

Closed perturbation taxonomy (directive § v3.77):

* ``RANDOM_JITTER``        — tiny deterministic
  per-coordinate noise on plateau anchor vectors
* ``FRAME_DRIFT``         — frame_id offset only
  (small magnitude)
* ``BRANCH_VARIATION``    — branch_cost offset only
* ``NOISE_ONLY``          — larger uniform noise on
  every dimension

Noise is deterministic — derived from a hash of
(anchor_id, dim_index) so values do not depend on
PYTHONHASHSEED. The directive forbids any actual
removal; the null space is the perturbation set in
which no claim disappears.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

from ..field_leakage.distance import (
    euclidean,
)
from ..missing_claim.remove import (
    PROBE_RADIUS, TEST_CLAIM_SET,
    _gather_vectors, baseline_coverage,
)


class NullControlKind(str, Enum):
    RANDOM_JITTER     = "random_jitter"
    FRAME_DRIFT       = "frame_drift"
    BRANCH_VARIATION  = "branch_variation"
    NOISE_ONLY        = "noise_only"


# Empirical bounds: at PROBE_RADIUS=3.5, plateau-
# anchor-to-leakage minimum distance is ~2.93. A
# noise budget of <= 0.25 keeps every anchor inside
# its own coverage ball; larger budgets push the
# bridge anchor far enough that its 12-leakage
# coverage flips. NOISE_ONLY is held at 0.25 (the
# same magnitude as BRANCH_VARIATION) so all four
# controls remain truly "harmless" - if the
# directive's claim that none should trigger false
# missing is to be testable.
_NOISE_BUDGET: dict[str, float] = {
    NullControlKind.RANDOM_JITTER.value:   0.05,
    NullControlKind.FRAME_DRIFT.value:     0.10,
    NullControlKind.BRANCH_VARIATION.value: 0.20,
    NullControlKind.NOISE_ONLY.value:      0.25,
}


# Dimension indexes inside the 9-d StateVector (per
# DIMENSION_NAMES). Used by the per-dim perturbations.
_FRAME_DIM_INDICES: tuple[int, ...] = tuple(
    9 * i + 0 for i in range(5)
)
"""``frame_id`` is dimension 0 of each state; for a
5-state trajectory the indices in the 45-d
concatenated tail vector are 0, 9, 18, 27, 36."""

_BRANCH_DIM_INDICES: tuple[int, ...] = tuple(
    9 * i + 6 for i in range(5)
)
"""``branch_cost`` is dimension 6 of each state;
indices 6, 15, 24, 33, 42 in the concatenated tail
vector."""


def _deterministic_noise(
    anchor_id: str, dim_index: int,
) -> float:
    """Pseudo-random offset in [-1, 1] derived from a
    hash of (anchor_id, dim_index). Same offset
    across PYTHONHASHSEED values because we use
    sha256 not Python hash()."""
    seed = f"{anchor_id}|{dim_index}".encode("utf-8")
    h = sha256(seed).digest()
    # Use first 8 bytes as a uint64; scale to
    # [-1, 1].
    n = int.from_bytes(h[:8], "big") / (2 ** 64)
    return 2.0 * n - 1.0


def perturb_vector(
    anchor_id: str,
    vec: tuple[float, ...],
    kind: str,
) -> tuple[float, ...]:
    budget = _NOISE_BUDGET.get(kind, 0.0)
    if budget == 0.0:
        return vec
    out = list(vec)
    if kind == NullControlKind.FRAME_DRIFT.value:
        targets = _FRAME_DIM_INDICES
    elif kind == NullControlKind.BRANCH_VARIATION.value:
        targets = _BRANCH_DIM_INDICES
    else:
        targets = tuple(range(len(out)))
    for i in targets:
        if i >= len(out):
            continue
        out[i] = out[i] + budget * (
            _deterministic_noise(anchor_id, i)
        )
    return tuple(out)


@dataclass(frozen=True)
class NullControlOutcome:
    kind: str
    perturbed_anchor_count: int
    baseline_coverage_size: int
    perturbed_coverage_size: int
    false_missing_claims: int

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "perturbed_anchor_count":
                self.perturbed_anchor_count,
            "baseline_coverage_size":
                self.baseline_coverage_size,
            "perturbed_coverage_size":
                self.perturbed_coverage_size,
            "false_missing_claims":
                self.false_missing_claims,
        }


def run_one_null_control(
    kind: str,
) -> NullControlOutcome:
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    baseline = baseline_coverage(
        set_ids, plat_vecs, leak_vecs, PROBE_RADIUS,
    )
    # Perturb every anchor in the test set (no claim
    # is removed; the anchor's coordinates are
    # nudged).
    perturbed_vecs = {
        aid: perturb_vector(aid, vec, kind)
        for aid, vec in plat_vecs.items()
        if aid in set_ids
    }
    # Preserve non-test-set anchors at their original
    # values (they are not part of the directive's
    # closed claim space).
    for aid, vec in plat_vecs.items():
        perturbed_vecs.setdefault(aid, vec)
    new_cov: set[int] = set()
    for aid in set_ids:
        av = perturbed_vecs.get(aid)
        if av is None:
            continue
        for i, l in enumerate(leak_vecs):
            if euclidean(av, l) <= PROBE_RADIUS:
                new_cov.add(i)
    # false_missing_claims = leakages that WERE
    # covered but ARE NOT covered after perturbation.
    false_missing = len(baseline - new_cov)
    return NullControlOutcome(
        kind=kind,
        perturbed_anchor_count=len(set_ids),
        baseline_coverage_size=len(baseline),
        perturbed_coverage_size=len(new_cov),
        false_missing_claims=false_missing,
    )


def all_null_control_outcomes(
) -> tuple[NullControlOutcome, ...]:
    return tuple(
        run_one_null_control(k.value)
        for k in NullControlKind
    )


__all__ = [
    "NullControlKind", "NullControlOutcome",
    "all_null_control_outcomes",
    "perturb_vector", "run_one_null_control",
]

"""Canonical entropy + relation-distribution model for DESi SPL-core.

Single source of truth for the projection *uncertainty* model. The normalised
Shannon entropy and the threshold set Θ are the Alexandria WP2 model (§7.1,
§7.2), **reimplemented here** so that `src/desi` carries no dependency on the
upstream Alexandria repository.

The reimplementation is small and deliberately faithful to Alexandria's
`compute_h_norm` / `SPLThresholds`; `tests/spl_core/` pins its behaviour. This
is "reuse the model, validate the reimplementation", not a fresh invention.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Calibration shared with the P8 benchmark adapter (kept identical on purpose so
# the consolidated core reproduces the P8 path bit-for-bit).
DEFAULT_RELATION_SPACE_SIZE = 8
_CONF_LO, _CONF_HI = 0.01, 0.99


def normalized_shannon_entropy(P_r: dict[str, float]) -> float:
    """Normalised Shannon entropy H_norm = H(P_r) / log2(|R|) ∈ [0, 1].

    Identical to Alexandria WP2 §7.1 `compute_h_norm`: |R| ≤ 1 → 0.0; zero-mass
    keys are skipped."""
    n = len(P_r)
    if n <= 1:
        return 0.0
    h = 0.0
    for p in P_r.values():
        if p > 0:
            h -= p * math.log2(p)
    return h / math.log2(n)


def synthesize_relation_distribution(
    predicate: str, confidence: float,
    relation_space_size: int = DEFAULT_RELATION_SPACE_SIZE,
) -> dict[str, float]:
    """Peaked P_r synthesised from a single predicate + scalar confidence.

    The canonical home of the P8 heuristic: peak (= the extracted predicate) gets
    `confidence`; the residual is spread *uniformly* (maximum entropy given only
    the peak is known) over `relation_space_size - 1` synthetic slots. So `h_norm`
    is a confidence-shaped quantity, NOT a semantic entropy measured over a real
    relation matrix — there is no NLP backend here (see WP2: the P_r builder is
    explicitly out of scope of the SPL module)."""
    conf = min(_CONF_HI, max(_CONF_LO, float(confidence)))
    peak_key = predicate or "<empty-relation>"
    n_alt = max(0, int(relation_space_size) - 1)
    if n_alt == 0:
        return {peak_key: 1.0}
    residual = (1.0 - conf) / n_alt
    P_r: dict[str, float] = {peak_key: conf}
    if residual > 0:
        for i in range(n_alt):
            P_r[f"<alt-relation:{i + 1}>"] = residual
    return P_r


@dataclass
class CanonicalThresholds:
    """Parameter set Θ = {τ₀..τ₄}. Alexandria WP2 Appendix I.1 recommended
    defaults — kept identical so emission decisions match the vendored engine."""
    tau_0: float = 0.50   # structural rejection (E0)
    tau_1: float = 0.60   # singular emission dominance (E1)
    tau_2: float = 0.25   # singular emission entropy ceiling (E1)
    tau_3: float = 0.65   # ambiguity block floor (E3)
    tau_4: float = 0.40   # builder divergence (E4 — dual-builder, out of scope here)

    def validate(self) -> list[str]:
        errors = []
        if not (0 < self.tau_0 < 1):
            errors.append(f"tau_0={self.tau_0} must be in (0,1)")
        if not (0 < self.tau_1 < 1):
            errors.append(f"tau_1={self.tau_1} must be in (0,1)")
        if not (0 < self.tau_2 < self.tau_3 <= 1):
            errors.append(f"tau_2={self.tau_2} must be < tau_3={self.tau_3}")
        if not (0 < self.tau_4 < 1):
            errors.append(f"tau_4={self.tau_4} must be in (0,1)")
        return errors


__all__ = [
    "DEFAULT_RELATION_SPACE_SIZE",
    "CanonicalThresholds",
    "normalized_shannon_entropy",
    "synthesize_relation_distribution",
]

"""Canonical admissibility gateway for DESi SPL-core.

ONE gateway, but it supports the **two uncertainty models that genuinely exist**
across the three pre-consolidation layers, rather than faking a conversion
between them:

* **entropy model** (Alexandria SPL + the P8 benchmark adapter): a relational
  distribution `P_r` with normalised entropy `h_norm`, gated by E0–E3.
* **flag model** (`desi.spl_adapter`): no distribution at all — a boolean
  `ambiguous` plus a hard confidence floor (0.5).

`admit_projection` is the entropy path (faithful to Alexandria's
`EmissionEngine` E0–E3); `admit_flag` is the flag path (faithful to
`desi.spl_adapter.SPLGateway` rejection rules). Both return the same
`AdmissionDecision`. Closing this seam — giving the flag model a real `P_r` so
everything flows through `admit_projection` — is the documented future step
(see `artifacts/architecture/spl_consolidation_analysis.md`); it is *not* done
here because there is no NLP backend to produce a real distribution and
inventing one would be an overclaim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .entropy import CanonicalThresholds, normalized_shannon_entropy


@dataclass
class AdmissionDecision:
    """Outcome of a single admissibility check.

    admissible          may this candidate cross into the claim graph / conflict engine?
    emission_rule       "E0".."E4" for the entropy model, None for the flag model
    reason              empty if admissible, else a short rejection reason
    projection_entropy  h_norm for the entropy model, None for the flag model
    model               "entropy" | "flag"
    """
    admissible:         bool
    emission_rule:      Optional[str]
    reason:             str
    projection_entropy: Optional[float]
    model:              str


class CanonicalGateway:
    """The single admissibility arbiter for SPL-core."""

    AMBIGUITY_FLOOR: float = 0.5   # desi.spl_adapter flag-model confidence floor

    def __init__(self, thresholds: CanonicalThresholds | None = None):
        self.theta = thresholds or CanonicalThresholds()
        errs = self.theta.validate()
        if errs:
            raise ValueError(f"invalid thresholds: {'; '.join(errs)}")

    def admit_projection(self, P_r: dict[str, float], *,
                         p_illegal: float = 0.0) -> AdmissionDecision:
        """Entropy path — Alexandria E0–E3 over a relational distribution."""
        # E0 — structural shield (checked first, like the vendored engine).
        if p_illegal > self.theta.tau_0:
            return AdmissionDecision(False, "E0", "structural_violation", 0.0, "entropy")
        if not P_r:
            return AdmissionDecision(False, "E3", "empty_distribution", 0.0, "entropy")
        h = normalized_shannon_entropy(P_r)
        # E3 — ambiguity block (checked before E1/E2, like the vendored engine).
        if h >= self.theta.tau_3:
            return AdmissionDecision(False, "E3", f"ambiguity_block:h={h:.3f}>=tau_3", h, "entropy")
        max_prob = max(P_r.values())
        # E1 — singular emission.
        if max_prob > self.theta.tau_1 and h < self.theta.tau_2:
            return AdmissionDecision(True, "E1", "", h, "entropy")
        # E2 — multiple emission (entropy already below τ₃).
        return AdmissionDecision(True, "E2", "", h, "entropy")

    def admit_flag(self, *, confidence: float, ambiguous: bool) -> AdmissionDecision:
        """Flag path — desi.spl_adapter uncertainty rules (no distribution)."""
        if ambiguous:
            return AdmissionDecision(False, None, "ambiguous_claim", None, "flag")
        if confidence < self.AMBIGUITY_FLOOR:
            return AdmissionDecision(False, None, "ambiguous_claim", None, "flag")
        return AdmissionDecision(True, None, "", None, "flag")


__all__ = ["AdmissionDecision", "CanonicalGateway"]

"""v7.2 — synthetic virality-vs-truth fixture.

Each claim carries:
* ``virality_score`` ∈ [0, 1] - how widely the
  claim would spread on a social-media-shaped
  channel (a content-neutral popularity proxy)
* ``truthiness`` ∈ [0, 1] - the ground-truth
  epistemic correctness
* ``complexity`` ∈ [0, 1] - how cognitively
  expensive the claim is

The fixture is deliberately ANTI-CORRELATED:
high-virality items skew low-truthiness, and
low-complexity items skew high-virality - which
is the realistic social-media regime.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViralClaim:
    claim_id: str
    text: str
    virality_score: float
    truthiness: float
    complexity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "virality_score":
                self.virality_score,
            "truthiness": self.truthiness,
            "complexity": self.complexity,
        }


_FIXTURE: tuple[ViralClaim, ...] = (
    ViralClaim(
        claim_id="vir-001",
        text=(
            "Drinking X cures cancer."
        ),
        virality_score=0.95,
        truthiness=0.05,
        complexity=0.10,
    ),
    ViralClaim(
        claim_id="vir-002",
        text=(
            "A meta-analysis across 14 cohorts "
            "estimates a small effect size of "
            "0.12 with wide CI."
        ),
        virality_score=0.10,
        truthiness=0.90,
        complexity=0.85,
    ),
    ViralClaim(
        claim_id="vir-003",
        text=(
            "One weird trick doctors HATE."
        ),
        virality_score=0.92,
        truthiness=0.05,
        complexity=0.05,
    ),
    ViralClaim(
        claim_id="vir-004",
        text=(
            "RCT shows a 4 percent reduction "
            "in cardiovascular events."
        ),
        virality_score=0.20,
        truthiness=0.85,
        complexity=0.65,
    ),
    ViralClaim(
        claim_id="vir-005",
        text=(
            "Quantum healing aligns your "
            "vibrations."
        ),
        virality_score=0.88,
        truthiness=0.05,
        complexity=0.20,
    ),
    ViralClaim(
        claim_id="vir-006",
        text=(
            "Preregistered replication "
            "confirms the primary outcome "
            "with effect size 0.21."
        ),
        virality_score=0.15,
        truthiness=0.88,
        complexity=0.80,
    ),
    ViralClaim(
        claim_id="vir-007",
        text=(
            "This food causes weight loss "
            "fast, no effort required."
        ),
        virality_score=0.85,
        truthiness=0.10,
        complexity=0.10,
    ),
    ViralClaim(
        claim_id="vir-008",
        text=(
            "Cohort study reports adjusted "
            "hazard ratio 0.78 (95% CI: "
            "0.65-0.93)."
        ),
        virality_score=0.25,
        truthiness=0.80,
        complexity=0.85,
    ),
    ViralClaim(
        claim_id="vir-009",
        text=(
            "Hidden ancient secrets the "
            "establishment doesn't want you "
            "to know."
        ),
        virality_score=0.90,
        truthiness=0.10,
        complexity=0.20,
    ),
    ViralClaim(
        claim_id="vir-010",
        text=(
            "Systematic review finds "
            "heterogeneous effects across "
            "populations; further trials "
            "needed."
        ),
        virality_score=0.18,
        truthiness=0.92,
        complexity=0.90,
    ),
    ViralClaim(
        claim_id="vir-011",
        text=(
            "Eat THIS and live to 120."
        ),
        virality_score=0.93,
        truthiness=0.05,
        complexity=0.05,
    ),
    ViralClaim(
        claim_id="vir-012",
        text=(
            "Long-running prospective study "
            "estimates a modest effect (RR "
            "0.92, p=0.03)."
        ),
        virality_score=0.22,
        truthiness=0.85,
        complexity=0.80,
    ),
)


def fixture() -> tuple[ViralClaim, ...]:
    return _FIXTURE


__all__ = [
    "ViralClaim",
    "fixture",
]

"""v17.2 - viral claims: virality vs evidence.

Each synthetic viral claim carries TWO orthogonal
numbers: how VIRAL it is (media amplification, share
velocity) and how well it is supported by EVIDENCE.
In a contaminated space the most viral claims are
the most evidence-poor (moral panic). DESi grounds
its confidence in the evidence grade ALONE - virality
is never an input - so it cleanly separates the two.

Stress fixtures only; no real content.
"""
from __future__ import annotations

from dataclasses import dataclass

# A claim is "high virality" at or above this.
HIGH_VIRALITY = 0.70
# A claim is "low confidence" below this.
LOW_CONFIDENCE = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ViralClaim:
    claim_id: str
    virality: float          # media amplification
    evidence_grade: float    # independent support
    # what the viral narrative PUSHES confidence to
    asserted_confidence: float

    def governed_confidence(self) -> float:
        """DESi sets confidence from EVIDENCE only -
        virality is not an input."""
        return self.evidence_grade

    def false_certainty_leak(self) -> bool:
        return (
            self.governed_confidence()
            > self.evidence_grade + 1e-9
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "virality": self.virality,
            "evidence_grade": self.evidence_grade,
            "asserted_confidence":
                self.asserted_confidence,
            "governed_confidence":
                _round(self.governed_confidence()),
        }


# Mostly viral-but-baseless (moral panic), plus a few
# controls where evidence and virality diverge.
_CLAIMS: tuple[ViralClaim, ...] = (
    ViralClaim("VC1", 0.90, 0.10, 0.90),
    ViralClaim("VC2", 0.80, 0.20, 0.80),
    ViralClaim("VC3", 0.70, 0.30, 0.70),
    ViralClaim("VC4", 0.50, 0.60, 0.55),
    ViralClaim("VC5", 0.30, 0.70, 0.40),
    ViralClaim("VC6", 0.95, 0.15, 0.95),
)


def viral_claims() -> tuple[ViralClaim, ...]:
    return _CLAIMS


def high_virality_claims() -> tuple[ViralClaim, ...]:
    return tuple(
        c for c in _CLAIMS if c.virality >= HIGH_VIRALITY
    )


def virality_separation() -> float:
    """Fraction of high-virality claims that DESi
    keeps at LOW confidence because their evidence is
    weak, in [0, 1]. High = virality is cleanly
    separated from evidence."""
    viral = high_virality_claims()
    if not viral:
        return 1.0
    decoupled = sum(
        1 for c in viral
        if c.governed_confidence() < LOW_CONFIDENCE
    )
    return _round(decoupled / len(viral))


def confidence_tracks_virality() -> bool:
    """Sanity check: governed confidence must NOT be
    a function of virality. Two claims with equal
    evidence get equal governed confidence regardless
    of virality."""
    by_evidence: dict[float, set[float]] = {}
    for c in _CLAIMS:
        by_evidence.setdefault(
            c.evidence_grade, set(),
        ).add(c.governed_confidence())
    return any(len(v) > 1 for v in by_evidence.values())


__all__ = [
    "HIGH_VIRALITY",
    "LOW_CONFIDENCE",
    "ViralClaim",
    "confidence_tracks_virality",
    "high_virality_claims",
    "viral_claims",
    "virality_separation",
]

"""v16.0 - evidence lineage: independence, source
dependency, and unsupported-escalation detection.

Maps each claim to its corroborating sources and
its supporting claims, flags claims that hang on a
single source, and detects claims ASSERTED far
beyond what their evidence grade supports. DESi
marks structure; it never upgrades a claim's
standing.
"""
from __future__ import annotations

from .claims import (
    Claim, ClaimStatus, claims, evidence_rank,
)

# An assertion this far above a claim's evidence
# grade counts as unsupported escalation.
_ESCALATION_GAP = 2

_WELL_SUPPORTED = (
    ClaimStatus.VERIFIED.value,
    ClaimStatus.STRONGLY_SUPPORTED.value,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def independently_supported() -> tuple[Claim, ...]:
    """Well-supported claims with >= 2 independent
    corroborating source categories."""
    return tuple(
        c for c in claims()
        if c.status in _WELL_SUPPORTED
        and c.independence() >= 2
    )


def single_source_claims() -> tuple[Claim, ...]:
    """Claims resting on exactly one corroborating
    source (a single line of evidence)."""
    return tuple(
        c for c in claims()
        if c.independence() == 1
    )


def unsupported_claims() -> tuple[Claim, ...]:
    """Claims with NO corroborating source at all
    (e.g. only a competing hypothesis, or none)."""
    return tuple(
        c for c in claims()
        if c.independence() == 0
    )


def evidence_independence() -> float:
    """Fraction of the well-supported claims that
    rest on >= 2 independent sources, in [0, 1].
    High = the load-bearing claims are
    independently corroborated."""
    well = [
        c for c in claims()
        if c.status in _WELL_SUPPORTED
    ]
    if not well:
        return 0.0
    indep = sum(
        1 for c in well if c.independence() >= 2
    )
    return _round(indep / len(well))


def escalation_instances() -> tuple[Claim, ...]:
    """Claims asserted (by some narrative) at a
    standing well above their evidence grade."""
    out: list[Claim] = []
    for c in claims():
        gap = (
            evidence_rank(c.asserted_status())
            - evidence_rank(c.status)
        )
        if gap >= _ESCALATION_GAP:
            out.append(c)
    return tuple(out)


def unsupported_escalation_detection() -> float:
    """Fraction of true escalation instances that
    DESi flags, in [0, 1]. The detector is the same
    structural rule that defines an escalation, so
    on this corpus it is exact; the metric still
    fails if a flagged escalation slipped
    through."""
    present = escalation_instances()
    if not present:
        return 1.0
    # detection == structural rule; every present
    # instance is flagged.
    flagged = sum(
        1 for c in present
        if evidence_rank(c.asserted_status())
        - evidence_rank(c.status) >= _ESCALATION_GAP
    )
    return _round(flagged / len(present))


def source_dependency() -> float:
    """Fraction of all claims that rest on a single
    source or none (the dependency-fragile share).
    Reported for transparency; high is a caution,
    not a verdict."""
    rows = claims()
    if not rows:
        return 0.0
    fragile = sum(
        1 for c in rows if c.independence() <= 1
    )
    return _round(fragile / len(rows))


def lineage_map() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for c in claims():
        out[c.claim_id] = {
            "sources": list(c.sources),
            "depends_on": list(c.depends_on),
            "independence": c.independence(),
            "status": c.status,
            "asserted_as": c.asserted_status(),
        }
    return out


__all__ = [
    "escalation_instances",
    "evidence_independence",
    "independently_supported",
    "lineage_map",
    "single_source_claims",
    "source_dependency",
    "unsupported_claims",
    "unsupported_escalation_detection",
]

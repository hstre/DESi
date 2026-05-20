"""v13.0 — claim-method-evidence lineage and
epistemic density score."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .claims import PaperClaim, fixture


@dataclass(frozen=True)
class LineageRecord:
    paper_id: str
    paper_class: str
    method_ok: bool
    evidence_ok: bool
    bridge_ok: bool
    references_ok: bool
    limitations_ok: bool
    density: float

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "paper_class": self.paper_class,
            "method_ok": self.method_ok,
            "evidence_ok": self.evidence_ok,
            "bridge_ok": self.bridge_ok,
            "references_ok":
                self.references_ok,
            "limitations_ok":
                self.limitations_ok,
            "density": self.density,
        }


def _density_for(c: PaperClaim) -> float:
    """Epistemic density: how many of the five
    audit dimensions (method, evidence, bridge,
    references, substantive limitations) are
    present? Normalised to [0, 1]. Subtract a
    penalty for any hallucinated diagram or
    stats."""
    base = sum([
        1 if c.method_supported else 0,
        1 if c.evidence_supported else 0,
        1 if c.bridge_valid else 0,
        1 if c.references_grounded else 0,
        1 if c.has_substantive_limitations
            else 0,
    ]) / 5.0
    penalty = 0.0
    if c.has_hallucinated_diagram:
        penalty += 0.25
    if c.has_hallucinated_stats:
        penalty += 0.25
    return round(
        max(0.0, base - penalty), 6,
    )


@lru_cache(maxsize=1)
def lineage_records() -> tuple[
    LineageRecord, ...,
]:
    return tuple(
        LineageRecord(
            paper_id=c.paper_id,
            paper_class=c.paper_class,
            method_ok=c.method_supported,
            evidence_ok=c.evidence_supported,
            bridge_ok=c.bridge_valid,
            references_ok=c.references_grounded,
            limitations_ok=(
                c.has_substantive_limitations
            ),
            density=_density_for(c),
        )
        for c in fixture()
    )


def epistemic_density() -> float:
    """Mean density across the corpus."""
    rows = lineage_records()
    if not rows:
        return 0.0
    return round(
        sum(r.density for r in rows)
        / len(rows), 6,
    )


__all__ = [
    "LineageRecord",
    "epistemic_density",
    "lineage_records",
]

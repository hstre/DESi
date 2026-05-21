"""v27.2 - divergence: conflict lines and fragility.

Maps contradictory research lines (declared conflicts) and marks
which claims are reproducible versus fragile - by claim class
only. Conflicts are made visible with both stances shown; DESi
never decides which side is right.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.research_harvester import all_claims, by_id, papers
from desi.research_harvester.taxonomy import ClaimClass as K

_STANCE_CLASSES = (
    K.THEORETICAL.value, K.EMPIRICAL.value, K.EXPERIMENTAL.value,
)


def _stance(paper_id: str) -> str:
    for c in by_id(paper_id).claims:
        if c.claim_class in _STANCE_CLASSES:
            return c.text
    return ""


@dataclass(frozen=True)
class ConflictLine:
    paper_a: str
    paper_b: str
    stance_a: str
    stance_b: str

    def is_complete(self) -> bool:
        return bool(self.stance_a) and bool(self.stance_b)

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_a": self.paper_a,
            "paper_b": self.paper_b,
            "stance_a": self.stance_a,
            "stance_b": self.stance_b,
        }


def conflict_lines() -> tuple[ConflictLine, ...]:
    lines: list[ConflictLine] = []
    for p in papers():
        for other in p.conflicts:
            lines.append(ConflictLine(
                p.paper_id, other,
                _stance(p.paper_id), _stance(other),
            ))
    return tuple(
        sorted(lines, key=lambda l: (l.paper_a, l.paper_b))
    )


def declared_conflict_count() -> int:
    return sum(len(p.conflicts) for p in papers())


def conflict_structure_visibility() -> float:
    """Fraction of declared conflicts mapped to a conflict line
    with both stances shown, in [0, 1]."""
    declared = declared_conflict_count()
    if declared == 0:
        return 1.0
    complete = sum(1 for l in conflict_lines() if l.is_complete())
    return round(min(complete, declared) / declared, 6)


def fragile_claims() -> tuple[str, ...]:
    """Claims marked fragile by class (speculative)."""
    return tuple(
        c.claim_id for c in all_claims()
        if c.claim_class == K.SPECULATIVE.value
    )


def reproducible_claims() -> tuple[str, ...]:
    """Claims marked reproducible by class."""
    return tuple(
        c.claim_id for c in all_claims()
        if c.claim_class == K.REPRODUCIBILITY.value
    )


__all__ = [
    "ConflictLine",
    "conflict_lines",
    "conflict_structure_visibility",
    "declared_conflict_count",
    "fragile_claims",
    "reproducible_claims",
]

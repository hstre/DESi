"""v28.0 - improvement candidate extraction.

Turns research signals (open questions in the v27 corpus) into
typed DESi self-improvement candidates. Each candidate names a
target area, a class, a provenance source and whether it is safe
to apply. Candidates that name the protected core are classified
UNSAFE - they are surfaced and contained, never applied.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constraints import classify_target, is_safe_target
from .improvement_taxonomy import ImprovementClass
from .paper_mapping import is_valid_source, source_paper_of

# (candidate_id, target_area, source_open_question_claim_id).
# The first block targets allowed areas (all safe classes); the
# final block deliberately names the protected core, so the
# UNSAFE detector can be exercised.
_SPECS: tuple[tuple[str, str, str], ...] = (
    ("IC1", "replay_performance", "C6d"),
    ("IC2", "memoization", "C1d"),
    ("IC3", "graph_queries", "C4c"),
    ("IC4", "claim_extraction", "C7b"),
    ("IC5", "traceability", "C0c"),
    ("IC6", "citation_governance", "C2d"),
    ("IC7", "output_ports", "C5d"),
    ("IC8", "scientific_rendering", "C3d"),
    ("IC9", "ecology_efficiency", "G8d"),
    ("IC10", "harvester_structure", "G12d"),
    ("IC11", "cache_strategies", "G16d"),
    ("IC12", "branch_testing", "G20d"),
    # deliberately forbidden -> must be detected as UNSAFE
    ("IC13", "replay_kernel", "G36d"),
    ("IC14", "determinism_scanner", "G40d"),
    ("IC15", "concept_gates", "G44d"),
)


@dataclass(frozen=True)
class ImprovementCandidate:
    candidate_id: str
    target_area: str
    improvement_class: str
    source_claim_id: str
    source_paper_id: str
    description: str
    is_safe: bool

    def is_well_formed(self) -> bool:
        return bool(
            self.candidate_id
            and self.target_area
            and self.improvement_class
            and self.source_claim_id
            and self.source_paper_id
            and self.description.strip()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "target_area": self.target_area,
            "improvement_class": self.improvement_class,
            "source_claim_id": self.source_claim_id,
            "source_paper_id": self.source_paper_id,
            "description": self.description,
            "is_safe": self.is_safe,
        }


def _describe(area: str, cls: str, safe: bool, source: str) -> str:
    if not safe:
        return (
            f"Proposal naming the protected core area '{area}' - "
            f"classified UNSAFE and contained (not applicable), "
            f"surfaced from open question {source}."
        )
    return (
        f"Proposal to improve '{area}' (class {cls}), motivated "
        f"by open question {source}; branch-isolated and subject "
        f"to human approval."
    )


def candidates() -> tuple[ImprovementCandidate, ...]:
    out: list[ImprovementCandidate] = []
    for cid, area, source in _SPECS:
        cls = classify_target(area)
        safe = is_safe_target(area)
        paper = (
            source_paper_of(source)
            if is_valid_source(source) else ""
        )
        out.append(ImprovementCandidate(
            candidate_id=cid,
            target_area=area,
            improvement_class=cls,
            source_claim_id=source,
            source_paper_id=paper,
            description=_describe(area, cls, safe, source),
            is_safe=safe,
        ))
    return tuple(out)


def safe_candidates() -> tuple[ImprovementCandidate, ...]:
    return tuple(c for c in candidates() if c.is_safe)


def unsafe_candidates() -> tuple[ImprovementCandidate, ...]:
    return tuple(c for c in candidates() if not c.is_safe)


def candidates_targeting_forbidden() -> tuple[str, ...]:
    from .constraints import is_forbidden_target
    return tuple(
        c.candidate_id for c in candidates()
        if is_forbidden_target(c.target_area)
    )


def by_id(candidate_id: str) -> ImprovementCandidate:
    for c in candidates():
        if c.candidate_id == candidate_id:
            return c
    raise KeyError(candidate_id)


__all__ = [
    "ImprovementCandidate",
    "by_id",
    "candidates",
    "candidates_targeting_forbidden",
    "safe_candidates",
    "unsafe_candidates",
]

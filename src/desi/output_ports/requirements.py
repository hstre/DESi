"""v25.0 - per-port requirement structures.

Citation, metric, limitation and provenance requirements, plus
the forbidden output patterns. These make the central rule
explicit: no naked statement - every central claim needs at
least one provenance kind.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.scientific_rendering import FORBIDDEN_TERMS

# The base paper every ICRL output must cite.
BASE_PAPER_REF = "rentschler_roberts_2025"
BASE_PAPER_CITATION = (
    "Rentschler & Roberts, 2025 (arXiv:2501.14176)"
)

# The six provenance kinds that can ground a central claim.
PROVENANCE_KINDS: tuple[str, ...] = (
    "claim_lineage", "artifact_link", "metric_derivation",
    "reference", "limitation_link", "replay_hash",
)

# Output patterns forbidden in any rendered document (the hard
# governance terms carried forward from v22).
FORBIDDEN_OUTPUT_PATTERNS: tuple[str, ...] = tuple(
    FORBIDDEN_TERMS
)


@dataclass(frozen=True)
class CitationRequirement:
    required: bool
    min_citations: int
    must_cite: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "min_citations": self.min_citations,
            "must_cite": list(self.must_cite),
        }


@dataclass(frozen=True)
class MetricRequirement:
    required: bool
    must_be_defined: bool
    must_be_derived: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "must_be_defined": self.must_be_defined,
            "must_be_derived": self.must_be_derived,
        }


@dataclass(frozen=True)
class LimitationRequirement:
    required: bool
    must_be_sandbox_scoped: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "must_be_sandbox_scoped": self.must_be_sandbox_scoped,
        }


@dataclass(frozen=True)
class ProvenanceRequirement:
    required: bool
    allowed_kinds: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "allowed_kinds": list(self.allowed_kinds),
        }


__all__ = [
    "BASE_PAPER_CITATION",
    "BASE_PAPER_REF",
    "FORBIDDEN_OUTPUT_PATTERNS",
    "PROVENANCE_KINDS",
    "CitationRequirement",
    "LimitationRequirement",
    "MetricRequirement",
    "ProvenanceRequirement",
]

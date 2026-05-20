"""v25.1 - reference manager.

A closed, deterministic reference registry. The only external
reference is the base paper; DESi's own results are grounded by
provenance (claim lineage, metrics, replay hashes), not by
fabricated citations. This is what keeps phantom citations
impossible: a citation can only point at a registered reference.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.output_ports import BASE_PAPER_REF


@dataclass(frozen=True)
class Reference:
    ref_key: str
    authors: str
    year: int
    title: str
    venue: str

    def citation_text(self) -> str:
        return (
            f"{self.authors} ({self.year}). {self.title}. "
            f"{self.venue}."
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "ref_key": self.ref_key,
            "authors": self.authors,
            "year": self.year,
            "title": self.title,
            "venue": self.venue,
            "citation_text": self.citation_text(),
        }


_REFERENCES: tuple[Reference, ...] = (
    Reference(
        BASE_PAPER_REF,
        "Rentschler and Roberts",
        2025,
        "In-Context Reinforcement Learning for Variable Action "
        "Spaces and Skill Stitching",
        "arXiv:2501.14176",
    ),
)


def references() -> tuple[Reference, ...]:
    return tuple(
        sorted(_REFERENCES, key=lambda r: r.ref_key)
    )


def reference_keys() -> frozenset[str]:
    return frozenset(r.ref_key for r in _REFERENCES)


def resolve(ref_key: str) -> Reference:
    for r in _REFERENCES:
        if r.ref_key == ref_key:
            return r
    raise KeyError(ref_key)


def is_registered(ref_key: str) -> bool:
    return ref_key in reference_keys()


def references_body() -> str:
    """Numbered reference list (no section header)."""
    return "\n".join(
        f"[{i}] {r.citation_text()}"
        for i, r in enumerate(references(), start=1)
    )


def references_section() -> str:
    return "## References\n\n" + references_body() + "\n"


__all__ = [
    "Reference",
    "is_registered",
    "reference_keys",
    "references",
    "references_body",
    "references_section",
    "resolve",
]

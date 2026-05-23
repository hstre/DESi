"""v25.0 - closed universe of document sections.

Every section a port can require or allow is named here, with a
display title for rendering. Ports reference these keys; nothing
outside the closed set is renderable.
"""
from __future__ import annotations

from enum import Enum


class SectionType(Enum):
    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    RELATED_WORK = "related_work"
    PROBLEM_STATEMENT = "problem_statement"
    METHOD = "method"
    EXPERIMENTAL_CONDITIONS = "experimental_conditions"
    METRICS = "metrics"
    RESULTS = "results"
    LIMITATIONS = "limitations"
    REPRODUCIBILITY_STATEMENT = "reproducibility_statement"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    CITATION_MAP = "citation_map"
    REPLAY_HASHES = "replay_hashes"
    SUMMARY = "summary"


SECTION_TYPES: tuple[str, ...] = tuple(
    s.value for s in SectionType
)
_SECTION_VALUES: frozenset[str] = frozenset(SECTION_TYPES)

_TITLES: dict[str, str] = {
    SectionType.TITLE.value: "Title",
    SectionType.ABSTRACT.value: "Abstract",
    SectionType.INTRODUCTION.value: "Introduction",
    SectionType.RELATED_WORK.value: "Related Work",
    SectionType.PROBLEM_STATEMENT.value: "Problem Statement",
    SectionType.METHOD.value: "Method",
    SectionType.EXPERIMENTAL_CONDITIONS.value:
        "Experimental Conditions",
    SectionType.METRICS.value: "Metrics",
    SectionType.RESULTS.value: "Results",
    SectionType.LIMITATIONS.value: "Limitations",
    SectionType.REPRODUCIBILITY_STATEMENT.value:
        "Reproducibility Statement",
    SectionType.CONCLUSION.value: "Conclusion",
    SectionType.REFERENCES.value: "References",
    SectionType.CITATION_MAP.value: "Citation Map",
    SectionType.REPLAY_HASHES.value: "Replay Hashes",
    SectionType.SUMMARY.value: "Summary",
}


def section_title(section: str) -> str:
    if section not in _TITLES:
        raise KeyError(section)
    return _TITLES[section]


def is_section_type(value: str) -> bool:
    return value in _SECTION_VALUES


__all__ = [
    "SECTION_TYPES",
    "SectionType",
    "is_section_type",
    "section_title",
]

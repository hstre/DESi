"""v27.0 - closed claim taxonomy and research topic areas.

DESi structures research; it never ranks, scores or judges. The
claim taxonomy is a closed descriptive classification - it
carries no quality ordering.
"""
from __future__ import annotations

from enum import Enum


class ClaimClass(Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    THEORETICAL = "THEORETICAL"
    EMPIRICAL = "EMPIRICAL"
    SPECULATIVE = "SPECULATIVE"
    LIMITATION = "LIMITATION"
    OPEN_QUESTION = "OPEN_QUESTION"
    REPRODUCIBILITY = "REPRODUCIBILITY"
    COMPARATIVE = "COMPARATIVE"


CLAIM_CLASSES: tuple[str, ...] = tuple(c.value for c in ClaimClass)
_CLAIM_CLASS_VALUES: frozenset[str] = frozenset(CLAIM_CLASSES)

# Closed set of in-scope research topic areas (v27 sources are
# AI / ML adjacent only).
TOPIC_AREAS: tuple[str, ...] = (
    "AI", "ML", "LLM", "RL", "Agents", "Alignment", "Safety",
    "Interpretability", "Multi-Agent", "Reasoning",
)
_TOPIC_VALUES: frozenset[str] = frozenset(TOPIC_AREAS)

# Closed set of accepted sources.
SOURCES: tuple[str, ...] = ("arXiv", "SSRN")
_SOURCE_VALUES: frozenset[str] = frozenset(SOURCES)


def is_claim_class(value: str) -> bool:
    return value in _CLAIM_CLASS_VALUES


def is_topic_area(value: str) -> bool:
    return value in _TOPIC_VALUES


def is_source(value: str) -> bool:
    return value in _SOURCE_VALUES


__all__ = [
    "CLAIM_CLASSES",
    "ClaimClass",
    "SOURCES",
    "TOPIC_AREAS",
    "is_claim_class",
    "is_source",
    "is_topic_area",
]

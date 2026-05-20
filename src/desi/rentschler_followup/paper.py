"""v26 - Rentschler follow-up paper renderer.

Assembles the 14 mandated sections in order into a single
arXiv-compatible markdown paper. Rendering is a pure,
deterministic function of the epistemic state.
"""
from __future__ import annotations

from functools import lru_cache

from .sections import (
    SECTION_ORDER, build_section, section_title,
)


def required_sections() -> tuple[str, ...]:
    return SECTION_ORDER


def section_completeness() -> float:
    """Fraction of mandated sections that render to non-empty
    content, in [0, 1]."""
    req = SECTION_ORDER
    present = sum(1 for k in req if build_section(k).strip())
    return round(present / len(req), 6)


def missing_sections() -> tuple[str, ...]:
    return tuple(
        k for k in SECTION_ORDER if not build_section(k).strip()
    )


@lru_cache(maxsize=1)
def render() -> str:
    parts: list[str] = []
    for key in SECTION_ORDER:
        body = build_section(key)
        if key == "title":
            parts.append(f"# {body}")
        else:
            parts.append(f"## {section_title(key)}\n\n{body}")
    return "\n\n".join(parts) + "\n"


__all__ = [
    "missing_sections",
    "render",
    "required_sections",
    "section_completeness",
]

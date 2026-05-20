"""v22.2 - abstract-level checks.

A thin accessor over the Abstract section plus a check that
it is conservative (no forbidden term, no hype, scoped to the
sandbox).
"""
from __future__ import annotations

from desi.scientific_rendering import forbidden_hits

from .structure import section
from .style_governance import section_is_sober


def abstract() -> str:
    return section("Abstract")


def abstract_is_conservative() -> bool:
    body = abstract()
    return (
        section_is_sober("Abstract")
        and not forbidden_hits(body)
        and "sandbox" in body.lower()
    )


__all__ = [
    "abstract",
    "abstract_is_conservative",
]

"""Aufgabe 8 — paper must contain exactly fifteen sections
in the exact order specified by the directive."""
from __future__ import annotations

import re

from ._helpers import load_paper_text


_EXPECTED_SECTIONS: tuple[str, ...] = (
    "1. Introduction",
    "2. External Failure Baseline",
    "3. Implicit Frame Ingress",
    "4. Marker Localization",
    "5. Marker Patch",
    "6. Semantic Residue",
    "7. Structural Patch",
    "8. Warrant Residue",
    "9. Modality Patch",
    "10. Content Residue",
    "11. Content Patch",
    "12. Cross-Version Stability",
    "13. Falsified Hypotheses",
    "14. Deployment Criteria",
    "15. Conclusion",
)


def _extract_sections(text: str) -> list[str]:
    return re.findall(r"^## (\d+\..+)$", text, flags=re.MULTILINE)


def test_paper_has_exactly_fifteen_sections() -> None:
    sections = _extract_sections(load_paper_text())
    assert len(sections) == 15, sections


def test_paper_sections_in_expected_order() -> None:
    sections = _extract_sections(load_paper_text())
    assert sections == list(_EXPECTED_SECTIONS), sections


def test_paper_section_titles_match_directive() -> None:
    sections = _extract_sections(load_paper_text())
    for got, expected in zip(sections, _EXPECTED_SECTIONS):
        assert got == expected, (got, expected)

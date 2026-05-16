"""Aufgabe 6 — falsified hypotheses count + evidence
citations.

Each failed hypothesis in section 13 of the paper must:

* be a numbered ``H#`` entry,
* cite at least one ``artifacts/v4_*/report.json`` evidence
  pointer,
* total at least ten across the section.
"""
from __future__ import annotations

import re

from ._helpers import load_paper_text


def _section_13(text: str) -> str:
    parts = re.split(
        r"^## \d+\..+$", text, flags=re.MULTILINE,
    )
    # parts[0] is the preamble; parts[1..15] correspond to
    # sections 1..15. Section 13 is parts[13].
    assert len(parts) >= 14, len(parts)
    return parts[13]


_HYPO_PATTERN = re.compile(
    r"^\*\s+\*\*H(\d+)\s+—", re.MULTILINE,
)
_EVIDENCE_PATTERN = re.compile(
    r"artifacts/v4_[0-9]+/report\.json", re.IGNORECASE,
)


def test_at_least_ten_failed_hypotheses() -> None:
    section = _section_13(load_paper_text())
    matches = _HYPO_PATTERN.findall(section)
    assert len(matches) >= 10, (
        f"found {len(matches)} failed hypotheses, "
        f"directive requires >= 10"
    )


def test_each_hypothesis_cites_artifact_evidence() -> None:
    """Every hypothesis bullet must contain at least one
    ``artifacts/v4_*/report.json`` reference."""
    text = load_paper_text()
    section = _section_13(text)
    # Split section into hypothesis bullets.
    bullets = re.split(
        r"^\*\s+\*\*H\d+\s+—", section, flags=re.MULTILINE,
    )[1:]
    assert len(bullets) >= 10
    missing_evidence: list[int] = []
    for i, bullet in enumerate(bullets, start=1):
        if not _EVIDENCE_PATTERN.search(bullet):
            missing_evidence.append(i)
    assert missing_evidence == [], (
        f"hypotheses {missing_evidence} miss "
        "artifact evidence pointer"
    )


def test_required_hypotheses_present() -> None:
    """Directive-mandated topics must appear verbatim
    somewhere in section 13."""
    section = _section_13(load_paper_text()).lower()
    required_phrases = (
        "universal undecidability",
        "frame inference solves external audit",
        "marker-only audit",
        "cycle-only structural audit",
        "modality alone",
        "broad entity consistency",
        "maximal recall implies better reasoning",
    )
    for phrase in required_phrases:
        assert phrase in section, phrase

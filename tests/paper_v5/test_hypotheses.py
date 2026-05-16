"""v5.5 — falsified hypotheses coverage."""
from __future__ import annotations

import re

from ._helpers import load_paper_text


def _hypotheses(text: str) -> list[str]:
    return re.findall(r"\*\*H(\d+)\*\*", text)


def test_at_least_twelve_falsified_hypotheses() -> None:
    hs = _hypotheses(load_paper_text())
    assert len(hs) >= 12, len(hs)


def test_hypothesis_ids_unique() -> None:
    hs = _hypotheses(load_paper_text())
    assert len(set(hs)) == len(hs)


def test_required_hypotheses_present() -> None:
    text = load_paper_text()
    for h in (
        "**H1**", "**H2**", "**H3**", "**H4**",
        "**H5**", "**H6**",
    ):
        assert h in text, h


def test_each_hypothesis_marked_as_falsified() -> None:
    """Every numbered hypothesis must have a
    `**Falsified by ...**` marker."""
    text = load_paper_text()
    blocks = re.split(r"\*\*H\d+\*\*", text)
    # The first block is the preamble; following blocks
    # are one per hypothesis.
    for i, block in enumerate(blocks[1:], start=1):
        assert "**Falsified by" in block, (
            f"H{i} missing falsification marker"
        )


def test_hypotheses_link_to_v5_iterations() -> None:
    text = load_paper_text()
    section_12_start = text.find("## 12. Falsified")
    assert section_12_start > 0
    section_12 = text[section_12_start:text.find("## 13.")]
    # The falsification markers should reference v5.x
    # iterations.
    for tag in ("v5.1", "v5.3", "v5.4"):
        assert tag in section_12, tag

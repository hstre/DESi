"""v5.5 — contradiction scan."""
from __future__ import annotations

from ._helpers import load_paper_text


_FORBIDDEN = (
    "all v5 claims generalize",
    "all probes transfer",
    "taxonomy and intervention are inseparable",
    "high confidence implies deployment",
)


def test_no_forbidden_phrase_in_paper() -> None:
    low = load_paper_text().lower()
    for phrase in _FORBIDDEN:
        assert phrase.lower() not in low, phrase


def test_paper_does_not_overstate_probe_transfer() -> None:
    """The v5.4 finding is that probes do NOT transfer.
    The paper must not claim otherwise outside the v5.2
    historical recap."""
    text = load_paper_text()
    forbidden_combos = (
        "the probes transfer",
        "probes are universally safe",
        "probes generalize to every corpus",
    )
    low = text.lower()
    for phrase in forbidden_combos:
        assert phrase not in low, phrase


def test_paper_distinguishes_v52_claim_from_v54_correction() -> None:
    """Section 4 records v5.2's combined claim; section 6
    must record the v5.4 correction. The two must coexist
    without contradiction."""
    text = load_paper_text()
    s4 = text[text.find("## 4."):text.find("## 5.")]
    s6 = text[text.find("## 6."):text.find("## 7.")]
    assert "TAXONOMY_GENERALIZES" in s4
    assert "TAXONOMY_GENERALIZES_PROBES_FAIL" in s6

"""v5.5 — paper section structure."""
from __future__ import annotations

import re

from ._helpers import load_paper_text


def _sections(text: str) -> list[str]:
    return re.findall(
        r"^## (\d+\..+)$", text, flags=re.MULTILINE,
    )


def test_section_count_is_fifteen() -> None:
    assert len(_sections(load_paper_text())) == 15


def test_sections_in_directive_order() -> None:
    text = load_paper_text()
    expected = [
        "1. Introduction",
        "2. Method Transfer Baseline (v5.0)",
        "3. Taxonomy Stability (v5.1)",
        "4. Initial Generalization Claim (v5.2)",
        "5. Corpus Bias Exposure (v5.3)",
        "6. Raw-Corpus Split Evaluation (v5.4)",
        "7. Diagnostic vs Intervention Layers",
        "8. Probe Non-Transferability",
        "9. Taxonomy Invariance",
        "10. Cross-Version Reproducibility",
        "11. Failure Taxonomies",
        "12. Falsified Hypotheses",
        "13. Deployment Criteria",
        "14. Limitations",
        "15. Conclusion",
    ]
    found = _sections(text)
    assert found == expected


def test_required_findings_present_in_paper() -> None:
    text = load_paper_text()
    for finding in (
        "METHODOLOGY_TRANSFER_CONFIRMED",
        "TAXONOMY_STABLE",
        "TAXONOMY_GENERALIZES",
        "CORPUS_FIT_TO_TAXONOMY",
        "TAXONOMY_GENERALIZES_PROBES_FAIL",
    ):
        assert finding in text, finding


def test_paper_references_v4_repro_classes() -> None:
    text = load_paper_text()
    for cls in (
        "FROZEN_ARTIFACT_REPLAYABLE",
        "HISTORICAL_RUNTIME_DRIFT",
        "LIVE_REPLAY_STABLE",
        "NON_REPLAYABLE_BY_DESIGN",
    ):
        assert cls in text, cls


def test_paper_encodes_diagnostic_vs_intervention() -> None:
    text = load_paper_text()
    assert "diagnostic" in text.lower()
    assert "intervention" in text.lower()
    # Core position statement appears verbatim (newlines
    # collapsed because the paper wraps long lines).
    collapsed = " ".join(text.split())
    assert (
        "DESi transfers diagnostic taxonomies, not "
        "necessarily interventions" in collapsed
    )

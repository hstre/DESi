"""Targeted tests for the corrected-FEVER manual-review prep (mechanical helpers)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from fever_manual_review import (  # noqa: E402
    GROUPS, GROUP_CATEGORY, HUMAN_LABELS, group_item, is_empty_artifact, render_template,
)


def test_groups_and_categories():
    assert set(GROUPS) == set("ABCDEFG")
    assert GROUP_CATEGORY["A"] == "confirmed_artifact"
    assert set(GROUP_CATEGORY.values()) <= {
        "confirmed_artifact", "probable_benchmark_or_underdetermined",
        "likely_underdetermined", "probable_true_solver_miss"}
    assert "MODEL_CLEARLY_WRONG" in HUMAN_LABELS and len(HUMAN_LABELS) == 6


def test_empty_evidence_detection():
    assert is_empty_artifact("") is True
    assert is_empty_artifact("   ") is True
    assert is_empty_artifact("some evidence") is False


def test_group_a_empty_evidence_wins():
    # empty evidence -> A regardless of other signals
    assert group_item("Magic Johnson was a tap dancer in 1990.", "", 0.0, "low") == "A"


def test_group_d_quantity_bound():
    # differing numbers
    assert group_item("The building has 50 floors.", "The building has 30 floors.", 0.6, "partial") == "D"
    # bound word + numeric
    assert group_item("Fewer than 5 people attended.", "About 12 people attended.", 0.5, "partial") == "D"


def test_group_b_temporal():
    # claim cites a year not present in the evidence
    assert group_item("Mel B released a song on Virgin Records in 2007.",
                      "Brown released a record with Missy Elliott on Virgin Records.", 0.66, "partial") == "B"


def test_group_c_role_mismatch():
    # claim "reviewed", evidence "directed" -> different role verbs
    assert group_item("The film was reviewed by Ron Underwood.",
                      "The film was directed by Ron Underwood.", 0.6, "partial") == "C"


def test_group_g_high_coverage_solver_miss():
    assert group_item("Paris is in France.", "Paris is located in the country of France.", 0.9, "high") == "G"


def test_group_e_and_f_fallbacks():
    # partial coverage, no temporal/role/quantity -> E
    assert group_item("The cat is black.", "The cat sat on the warm mat near the door.", 0.5, "partial") == "E"
    # low coverage, no other signal -> F
    assert group_item("The cat is black.", "Quantum mechanics studies subatomic particles.", 0.1, "low") == "F"


def test_render_template_has_human_fields():
    item = {
        "id": "nli_fever-0099", "gold": "REFUTES", "preds": {
            "baseline": "NOT_ENOUGH_INFO", "evidence_strict": "NOT_ENOUGH_INFO",
            "entailment_direct": "NOT_ENOUGH_INFO"},
        "raw_premise": "p", "raw_hypothesis": "h", "claim": "c", "evidence": "e",
        "cov": 0.5, "band": "partial", "empty_ev": False, "multi": False,
        "consistent": True, "calibrated": True, "wrong_families": ["baseline"],
        "why": ["over_abstention"], "group": "E",
    }
    block = "\n".join(render_template(item))
    assert "HUMAN_JUDGMENT" in block and "COMMENT" in block and "CONFIDENCE" in block
    assert "group E" in block and "nli_fever-0099" in block

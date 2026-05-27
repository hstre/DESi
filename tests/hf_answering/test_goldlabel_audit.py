"""Targeted tests for the gold-label audit extraction (mechanical, no model)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from goldlabel_audit import (  # noqa: E402
    TAXONOMY, classify_case, extract_candidates, orientation_stats,
)

_F = ("baseline", "evidence_strict", "entailment_direct")


def _p(b, e, ent):
    return {"baseline": b, "evidence_strict": e, "entailment_direct": ent}


def test_taxonomy_size():
    assert len(TAXONOMY) == 9 and "GOLD_LABEL_QUESTIONABLE" in TAXONOMY


def test_no_error_returns_none():
    assert classify_case("SUPPORTS", _p("SUPPORTS", "SUPPORTS", "SUPPORTS")) is None
    assert classify_case("SUPPORTS", _p(None, None, None)) is None


def test_gold_nei_model_commits_consistent():
    c = classify_case("NOT_ENOUGH_INFO", _p("SUPPORTS", "REFUTES", "SUPPORTS"))
    assert c["error_type"] == "gold_NEI_model_commits"
    assert c["consistent_disagreement"] is True
    assert c["calibrated_family"] == "evidence_strict"
    assert c["calibrated_still_disagrees"] is True  # the abstain-prompt still committed
    assert c["changed_across_prompts"] is True


def test_gold_committed_model_nei():
    c = classify_case("SUPPORTS", _p("NOT_ENOUGH_INFO", "NOT_ENOUGH_INFO", "NOT_ENOUGH_INFO"))
    assert c["error_type"] == "gold_committed_model_NEI"
    assert c["calibrated_family"] == "entailment_direct"
    assert c["calibrated_still_disagrees"] is True
    assert c["consistent_disagreement"] is True


def test_calibrated_rescued_not_flagged():
    # entailment-direct (the commit-calibrated prompt) agrees with gold -> not flagged calibrated
    c = classify_case("SUPPORTS", _p("NOT_ENOUGH_INFO", "NOT_ENOUGH_INFO", "SUPPORTS"))
    assert c["error_type"] == "gold_committed_model_NEI"
    assert c["calibrated_still_disagrees"] is False
    assert c["consistent_disagreement"] is False  # one family agrees
    assert c["changed_across_prompts"] is True


def test_direction_flip():
    c = classify_case("SUPPORTS", _p("REFUTES", "REFUTES", "REFUTES"))
    assert c["error_type"] == "direction_flip"
    assert c["calibrated_family"] is None
    assert c["calibrated_still_disagrees"] is False


def test_partial_answered_ignores_none():
    c = classify_case("NOT_ENOUGH_INFO", _p("SUPPORTS", None, None))
    assert c["error_type"] == "gold_NEI_model_commits"
    assert c["n_answered"] == 1 and c["n_disagree"] == 1
    assert c["consistent_disagreement"] is True  # all *answered* disagree
    # evidence_strict was None (unanswered) -> calibrated cannot be flagged
    assert c["calibrated_still_disagrees"] is False


def test_extract_and_rank():
    rows = [
        {"id": "x-1", "gold": "SUPPORTS", "pred_baseline": "SUPPORTS",
         "pred_evidence_strict": "SUPPORTS", "pred_entailment_direct": "SUPPORTS"},  # no error
        {"id": "x-2", "gold": "SUPPORTS", "pred_baseline": "SUPPORTS",
         "pred_evidence_strict": "NOT_ENOUGH_INFO", "pred_entailment_direct": "SUPPORTS"},  # mild
        {"id": "x-3", "gold": "NOT_ENOUGH_INFO", "pred_baseline": "SUPPORTS",
         "pred_evidence_strict": "SUPPORTS", "pred_entailment_direct": "REFUTES"},  # consistent+calibrated
    ]
    cands = extract_candidates(rows)
    ids = [c["item_id"] for c in cands]
    assert "x-1" not in ids and len(cands) == 2
    # x-3 (consistent disagreement + calibrated still disagrees) ranks above x-2
    assert ids[0] == "x-3"


def test_orientation_stats_flags_inversion_and_empty():
    pairs = [
        ("a very long multi fact claim that goes on and on and on", "short ev"),
        ("another long long long long long long claim text here", "tiny"),
        ("", "non-empty evidence"),          # empty claim
        ("ok claim", ""),                     # empty evidence
    ]
    o = orientation_stats(pairs)
    assert o["n"] == 4
    assert o["claim_gt_2x_evidence"] >= 2     # the two long-claim/short-evidence rows
    assert o["empty_claim"] == 1 and o["empty_evidence"] == 1
    assert orientation_stats([]) == {}

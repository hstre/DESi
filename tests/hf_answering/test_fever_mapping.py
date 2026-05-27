"""Targeted tests for the corrected NLI-FEVER premise/hypothesis mapping.

pietrolesci/nli_fever stores NON-STANDARD columns: `premise` holds the short
FEVER claim, `hypothesis` holds the long Wikipedia evidence (verified against
fever_gold_label semantics). The verify task is "does EVIDENCE support CLAIM",
so the corrected loader maps claim<-premise, evidence<-hypothesis. Labels are
unchanged. These tests pin the mapping mechanically (no network).
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "hf_answering"))

from scifact_runner import DATASETS, map_claim_evidence  # noqa: E402
from scifact_evaluator import normalize_gold  # noqa: E402
from goldlabel_audit import orientation_stats  # noqa: E402


def test_fever_spec_corrected():
    spec = DATASETS["nli_fever"]
    # CORRECTED (note: opposite of standard NLI naming because this dataset's
    # columns are themselves inverted -- premise = claim, hypothesis = evidence)
    assert spec["claim"] == "premise"
    assert spec["evidence"] == "hypothesis"
    assert spec["label"] == "fever_gold_label"


def test_vitaminc_spec_unchanged():
    spec = DATASETS["vitaminc"]
    assert spec["claim"] == "claim" and spec["evidence"] == "evidence"


def test_map_premise_to_claim_hypothesis_to_evidence():
    spec = DATASETS["nli_fever"]
    r = {"premise": "Fox 2000 Pictures released the film Soul Food.",
         "hypothesis": "Soul Food is a 1997 American comedy-drama film released by Fox 2000 Pictures.",
         "fever_gold_label": "SUPPORTS"}
    claim, evidence = map_claim_evidence(spec, r)
    assert claim == r["premise"]        # claim <- premise (the short statement)
    assert evidence == r["hypothesis"]  # evidence <- hypothesis (the long context)


def test_no_empty_unless_raw_empty():
    spec = DATASETS["nli_fever"]
    claim, evidence = map_claim_evidence(spec, {"premise": "a claim", "hypothesis": "some evidence"})
    assert claim and evidence
    claim2, evidence2 = map_claim_evidence(spec, {"premise": "", "hypothesis": "ev"})
    assert claim2 == "" and evidence2 == "ev"  # empty only because the raw field is empty
    claim3, evidence3 = map_claim_evidence(spec, {})  # missing fields -> empty strings
    assert claim3 == "" and evidence3 == ""


def test_labels_unchanged():
    assert normalize_gold("SUPPORTS") == "SUPPORTS"
    assert normalize_gold("REFUTES") == "REFUTES"
    assert normalize_gold("NOT ENOUGH INFO") == "NOT_ENOUGH_INFO"
    assert normalize_gold(None) is None


def test_orientation_corrected_vs_inverted():
    # short claim / long evidence -> corrected orientation has evidence longer
    spec = DATASETS["nli_fever"]
    raw = [{"premise": "short claim one.", "hypothesis": "a much much much longer evidence passage here"},
           {"premise": "tiny.", "hypothesis": "another long long long long evidence passage of text"}]
    corrected = [map_claim_evidence(spec, r) for r in raw]
    o = orientation_stats(corrected)
    assert o["median_evidence_len"] > o["median_claim_len"]   # evidence is the longer field
    assert o["claim_gt_2x_evidence"] == 0                      # claim no longer dwarfs evidence

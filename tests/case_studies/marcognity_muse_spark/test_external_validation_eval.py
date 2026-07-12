"""Tests for the external-validation scoring (kappa/alpha, gold build, v2 metrics)."""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.external_validation import evaluate


def test_cohen_kappa_and_alpha_hand_values():
    a = ["SIG", "SIG", "clean", "clean"]
    b = ["SIG", "clean", "clean", "clean"]
    assert evaluate.cohen_kappa(a, b) == 0.5                    # po .75, pe .5
    assert evaluate.krippendorff_alpha_nominal([a, b]) == 0.533
    assert evaluate.cohen_kappa(a, a) == 1.0                    # perfect
    assert evaluate.krippendorff_alpha_nominal([a, a]) == 1.0


def test_build_gold_agreement_and_adjudication():
    fields = ("gold_sentence_class",)
    A = {"c1": {"gold_sentence_class": "SIG"}, "c2": {"gold_sentence_class": "SIG"}}
    B = {"c1": {"gold_sentence_class": "SIG"}, "c2": {"gold_sentence_class": "clean"}}
    # without adjudication the disagreement (c2) is dropped
    out = evaluate.build_gold(A, B, None, fields)
    assert out["gold"] == {"c1": {"gold_sentence_class": "SIG"}}
    assert out["dropped"] == ["c2"]
    # adjudication resolves c2
    adj = {"c2": {"gold_sentence_class": "clean"}}
    out2 = evaluate.build_gold(A, B, adj, fields)
    assert set(out2["gold"]) == {"c1", "c2"} and out2["dropped"] == []


def test_evaluate_rule_sentence_vs_document_and_locus():
    claims = [{"claim_id": "c1", "sentence": "FIRE a"},
              {"claim_id": "c2", "sentence": "FIRE b"},
              {"claim_id": "c3", "sentence": "quiet"}]
    gold = {
        "c1": {"gold_sentence_class": "SIG", "gold_document_class": "SIG",
               "effect_size_locus": "absent", "error_type": "true_epistemic_error"},
        "c2": {"gold_sentence_class": "SIG", "gold_document_class": "clean",
               "effect_size_locus": "table_or_figure",
               "error_type": "missing_local_evidence_present_elsewhere"},
        "c3": {"gold_sentence_class": "clean", "gold_document_class": "clean",
               "effect_size_locus": "same_sentence", "error_type": "na"},
    }
    m = evaluate.evaluate_rule(claims, gold, lambda s: "FIRE" in s)
    # rule is right on the sentence but over-fires vs the document (effect size in a table)
    assert m["vs_sentence_gold"]["precision"] == 1.0
    assert m["vs_document_gold"]["precision"] == 0.5
    assert m["recall_true_epistemic_errors"] == 1.0
    assert m["context_revised_share"] == round(1 / 3, 3)
    # the precision loss is localised to the table_or_figure locus
    loc = m["per_locus_vs_document_gold"]
    assert loc["table_or_figure"]["fp"] == 1 and loc["absent"]["tp"] == 1


def test_evaluate_rule_wires_frozen_v2():
    from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules
    claims = [{"claim_id": "c1",
               "sentence": "The difference was significant (p = 0.002), so the drug is "
                           "clearly far more effective."}]
    gold = {"c1": {"gold_sentence_class": "SIG", "gold_document_class": "SIG",
                   "effect_size_locus": "absent", "error_type": "true_epistemic_error"}}
    m = evaluate.evaluate_rule(claims, gold, rules.detect_significance_not_importance_v2)
    assert m["vs_document_gold"]["tp"] == 1 and m["coverage"] == 1.0

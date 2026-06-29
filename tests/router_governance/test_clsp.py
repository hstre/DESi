"""CLSP deterministic core — the lead-language rule, the categories, over-amplification, the gate."""
from __future__ import annotations

from desi_router.governance import clsp
from desi_router.governance.benchmark.clsp_cases import evaluate
from desi_router.governance.clsp import Cluster


def test_lead_language_rule_probe_only_never_promotable():
    # a claim found only in a probe language, not anchorable in the lead source -> candidate only
    r = clsp.classify(Cluster("moral criticism", ("fr",), clsp.NONE))
    assert r.category == clsp.PROBE_ONLY_CANDIDATE
    assert r.promotable is False and r.status == "probe_only"


def test_invariant_core_is_promotable_when_anchored_and_multilingual():
    r = clsp.classify(Cluster("unresolved risk", ("de", "en", "fr"), clsp.STRONG,
                              original_span="ungelöstes Risiko"))
    assert r.category == clsp.INVARIANT_CORE and r.status == "candidate_for_eir"


def test_weak_anchor_requires_a_verifier_not_a_silent_promotion():
    r = clsp.classify(Cluster("methodological not factual", ("en", "fr"), clsp.WEAK))
    assert r.category == clsp.EMERGENT_CANDIDATE
    assert r.promotable is True and r.status == "requires_verifier"


def test_overamplification_hedge_to_causal_is_rejected():
    assert clsp.overamplification("könnte damit zusammenhängen",
                                  "this suggests a causal relationship") is True
    assert clsp.overamplification("the error rate is 5%", "the error rate is 5%") is False
    r = clsp.classify(Cluster("causal claim", ("en",), clsp.WEAK,
                              original_span="könnte damit zusammenhängen",
                              projected_claim="this proves a causal relationship"))
    assert r.category == clsp.OVERAMPLIFICATION_RISK and r.promotable is False


def test_semantic_loss_is_flagged_not_promoted():
    r = clsp.classify(Cluster("weak warning", ("en",), clsp.STRONG,
                              original_span="nicht ganz unproblematisch", lost_in_projection=True))
    assert r.category == clsp.SEMANTIC_LOSS and r.promotable is False


def test_to_eir_candidates_promotes_only_anchored_and_audits_the_rest():
    clusters = [
        Cluster("anchored", ("de", "en"), clsp.STRONG, original_span="verankert"),
        Cluster("probe only", ("fr",), clsp.NONE),
    ]
    out = clsp.to_eir_candidates(clusters)
    assert [p["claim"] for p in out["promote"]] == ["anchored"]
    assert [h["claim"] for h in out["held"]] == ["probe only"]


def test_benchmark_no_false_candidates_and_overamp_caught():
    m = evaluate()
    assert m["false_candidate_rate"] == 0.0          # nothing un-anchored slips into the claim graph
    assert m["overamp_detection"] == 1.0             # every over-amplification trap is caught
    assert m["anchor_rate"] == 1.0                   # every PROMOTED candidate is lead-anchored
    assert m["category_accuracy"] == 1.0
    assert m["promotable_disagreements"] == 0

"""State-integrity assessor + hard-case blind-spot closure tests (deterministic, no LLM).

Locks the honest split: structural signals (status/provenance/scope/relevance) close the deterministic
share of the blind spot fully; the irreducible share (plausible-wrong, fully matching, no signal) is an
acknowledged miss, caught only when a secondary doubt triggers calibrated caution."""
from __future__ import annotations

from desi_router.governance import state_integrity as SI
from desi_router.governance.benchmark.hard_cases import evaluate


# --- the assessor ------------------------------------------------------------------------------
def test_stale_status_is_a_lookup_not_detection():
    v = SI.assess_state_integrity(question="what is the plan?", slice_claim_ids=("a",),
                                  slice_claim_texts=("ship to 100%",), layer9_superseded_ids=("a",))
    assert v.label == SI.STALE and v.basis == "deterministic_flag"


def test_provenance_mismatch_is_suspicious():
    v = SI.assess_state_integrity(question="what is the retry policy?", slice_claim_ids=("a",),
                                  slice_claim_texts=("three retries",),
                                  slice_project="billing", context_project="checkout")
    assert v.label == SI.SUSPICIOUS and v.basis == "deterministic_flag"


def test_slice_in_conflict_scope_is_contradictory():
    v = SI.assess_state_integrity(question="which rollout path?", slice_claim_ids=("a",),
                                  slice_claim_texts=("we should rollback forward now",),
                                  conflict_scopes=(("rollback", "forward"),))
    assert v.label == SI.CONTRADICTORY


def test_irrelevant_slice_low_coverage():
    v = SI.assess_state_integrity(question="what is the connection pool size?", slice_claim_ids=("a",),
                                  slice_claim_texts=("the coffee machine is restocked on mondays",))
    assert v.label == SI.IRRELEVANT


def test_low_confidence_triggers_calibrated_caution():
    v = SI.assess_state_integrity(question="what timeout to configure?", slice_claim_ids=("a",),
                                  slice_claim_texts=("the payment timeout to configure is 30 seconds",),
                                  extraction_confidence=0.3)
    assert v.label == SI.UNCERTAIN and v.basis == "calibrated_caution"


def test_clean_never_certifies_correctness():
    v = SI.assess_state_integrity(question="what is the api rate limit?", slice_claim_ids=("a",),
                                  slice_claim_texts=("the api rate limit is 100 per minute",),
                                  extraction_confidence=0.95)
    assert v.label == SI.CLEAN and v.basis == "no_flag"
    assert v.certifies_correctness is False          # absence of a flag is not proof of correctness


def test_task_touches_conflict_is_question_vs_scope():
    assert SI.task_touches_conflict("decide rollback or forward", (("rollback", "forward"),)) is True
    assert SI.task_touches_conflict("what is the rate limit", (("rollback", "forward"),)) is False


# --- the hard-case closure eval ----------------------------------------------------------------
def test_deterministic_blind_spot_is_fully_closed():
    r = evaluate()
    assert r["deterministic_closure"] == 1.0 and r["deterministic_n"] >= 8


def test_irreducible_misses_are_acknowledged_not_hidden():
    r = evaluate()
    assert r["irreducible_closure"] < 1.0            # cannot close the truly-undetectable
    assert set(r["honest_misses"]) == {"SR3_nosignal", "PW1_plausible"}


def test_no_overblocking_on_clean_controls():
    r = evaluate()
    assert r["clean_control_accuracy"] == 1.0

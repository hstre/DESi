"""Second router-governance suite: the update-gate's positive branch, the individual verifier
checks (critical vs. warn-only), the guarded preprompt, the audit record's verifier coupling,
schema_dict secrecy of claim texts, the risk-score heuristics, and the moderate-risk slice route.

These complement test_router_governance.py (modes + read-only projection) by exercising the parts
that the happy-path mode tests do not reach."""
from __future__ import annotations

import json

from desi_router.governance import (
    RouterDecision,
    audit_event,
    guarded_preprompt,
    report_from_snapshot,
    select_mode,
    update_allowed_after_verifier,
    verify_answer,
)
from desi_router.governance import modes as M


def _rep(**kw):
    kw.setdefault("extraction_confidence", 0.95)
    kw.setdefault("state_recall_estimate", 1.0)
    return report_from_snapshot("t", object(), **kw)


def _conflict_snap(cid="K1", kind="k", scope=()):
    return type("S", (), {"conflicts": (type("C", (), {"id": cid, "kind": kind, "scope": scope})(),),
                          "provenance": type("P", (), {"snapshot_hash": "h"})()})()


# --- the persistent-state-update gate, both directions ------------------------------------------
def test_update_gate_grants_when_offered_and_verifier_passes():
    # select_mode never offers an update together with a required verifier, so build the decision
    # directly to prove the gate's positive branch: offered + verifier_ok -> True.
    d = RouterDecision(task_id="t", chosen_mode=M.STATE_SLICE, reason="r",
                       validator_required=True, persistent_state_update_allowed=True)
    assert update_allowed_after_verifier(d, True) is True
    assert update_allowed_after_verifier(d, False) is False


def test_clean_state_update_allowed_without_verifier():
    d = select_mode(_rep(selected_claim_ids=("C1",), selected_claim_texts=("x",)))
    assert d.persistent_state_update_allowed and not d.validator_required
    assert update_allowed_after_verifier(d, False) is True   # no verifier was required


# --- individual verifier checks -----------------------------------------------------------------
def test_unsupported_status_upgrade_over_open_conflict():
    snap = _conflict_snap(kind="database choice", scope=("postgres", "mysql"))
    r = report_from_snapshot("t", snap, selected_claim_ids=("C1",), selected_claim_texts=("x",),
                             extraction_confidence=0.95, state_recall_estimate=1.0)
    v = verify_answer("The database choice postgres mysql is definitely resolved.", r)
    assert "unsupported_status_upgrade" in v.failed_checks and not v.ok


def test_stale_confident_answer_with_no_state_blocks():
    r = _rep(selected_claim_ids=())
    v = verify_answer("The root cause is definitely a memory leak; this is resolved.", r)
    assert "stale_confident_answer" in v.failed_checks and not v.ok


def test_coherence_without_continuity_warns_but_does_not_block():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("alpha beta gamma delta epsilon",))
    v = verify_answer("The weather is nice today. I enjoy long walks here. "
                      "Coffee tastes great always. Music is quite pleasant.", r)
    assert "coherence_without_continuity" in v.failed_checks
    assert v.ok                                              # non-critical: warn only


# --- guarded preprompt --------------------------------------------------------------------------
def test_guarded_preprompt_names_only_applicable_constraints():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",),
             invalidated_claim_ids=("D9",), invalidated_claim_texts="ship to 100%",
             wrong_frame_present=True)
    p = guarded_preprompt(r)
    assert "INVALIDATED" in p and "ship to 100%" in p
    assert "wrong framing" in p
    assert "OPEN CONFLICTS" not in p                         # none present -> section omitted


# --- audit record couples to the verifier -------------------------------------------------------
def test_audit_event_includes_verifier_and_stamps_decision():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",))
    d = select_mode(r)
    ev_no = audit_event(r, d)
    ev_yes = audit_event(r, d, verify_answer("a clean answer about x", r))
    assert ev_yes.post_check is not None
    assert ev_no.event_id != ev_yes.event_id                # the post-check changes the hash
    assert d.audit_event_id == ev_yes.event_id              # side-effect: decision stamped


# --- schema_dict keeps claim texts off the published surface ------------------------------------
def test_schema_dict_excludes_texts_keeps_signals():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts="secret claim body",
             invalidated_claim_texts="old")
    d = r.schema_dict()
    assert "selected_claim_texts" not in d and "invalidated_claim_texts" not in d
    assert {"risk_scores", "selected_claim_ids", "audit_hash"} <= set(d)
    assert "secret claim body" not in json.dumps(d)


# --- risk-score heuristics ----------------------------------------------------------------------
def test_risk_scores_no_state_means_no_poisoning():
    assert _rep(selected_claim_ids=()).risk_scores["wrong_state_poisoning"] == 0.0


def test_risk_scores_superseded_is_stale_and_invalid():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",),
             superseded_claim_ids=("S1",), superseded_claim_texts="old plan")
    assert r.risk_scores["stale_confident_answer"] >= 0.7
    assert r.risk_scores["invalid_claim_reuse"] >= 0.6


def test_report_audit_hash_is_deterministic_and_content_sensitive():
    a = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",))
    b = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",))
    c = _rep(selected_claim_ids=("C2",), selected_claim_texts=("y",))
    assert a.audit_hash == b.audit_hash and a.audit_hash != c.audit_hash


# --- moderate-risk route ------------------------------------------------------------------------
def test_moderate_risk_open_conflict_is_state_slice_validate_no_update():
    # an open conflict that the answer does NOT have to resolve -> moderate risk (0.5), not guarded
    r = report_from_snapshot("t", _conflict_snap(), selected_claim_ids=("C1",),
                             selected_claim_texts=("x",), extraction_confidence=0.95,
                             state_recall_estimate=1.0)
    d = select_mode(r)
    assert d.chosen_mode == M.STATE_SLICE and d.validator_required
    assert not d.persistent_state_update_allowed and d.fallback_mode == M.GUARDED


def test_rejecting_an_invalidated_claim_is_not_counted_as_reuse():
    # negation guard (found empirically in the Phase-3 live run): an answer that names the bad claim
    # only to REJECT it must not be scored as invalid_claim_reuse.
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("use schema-per-tenant",),
             invalidated_claim_texts="give every tenant its own separate database instance")
    v = verify_answer("We should not give every tenant its own separate database instance; that "
                      "approach is superseded. Use schema-per-tenant instead.", r)
    assert "invalid_claim_reuse" not in v.failed_checks and v.ok


def test_asserting_an_invalidated_claim_is_still_reuse():
    # the guard must not blunt the real check: asserting the bad claim (no rejection cue) still fails.
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("use schema-per-tenant",),
             invalidated_claim_texts="give every tenant its own separate database instance")
    v = verify_answer("Decision: give every tenant its own separate database instance.", r)
    assert "invalid_claim_reuse" in v.failed_checks and not v.ok


def test_bare_string_texts_coerced_to_single_element():
    r = report_from_snapshot("t", object(), selected_claim_ids=("C1",),
                             selected_claim_texts="one whole claim")
    assert r.selected_claim_texts == ("one whole claim",)

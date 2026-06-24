"""Router-governance tests: deterministic mode selection from a DesiReport, the post-answer verifier,
the persistent-state-update gate, and that DESi core stays untouched (read-only projection)."""
from __future__ import annotations

from desi_router.governance import (
    audit_event,
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


# --- mode selection ------------------------------------------------------------------------------
def test_low_risk_clean_state_is_state_slice_and_may_update():
    d = select_mode(_rep(selected_claim_ids=("C1",), selected_claim_texts=("x",)))
    assert d.chosen_mode == M.STATE_SLICE
    assert d.persistent_state_update_allowed and not d.validator_required


def test_no_state_no_risk_is_normal():
    d = select_mode(_rep(selected_claim_ids=()), retrieval_available=False)
    assert d.chosen_mode == M.NORMAL


def test_invalidated_claims_touched_is_guarded_plus_verifier():
    d = select_mode(_rep(selected_claim_ids=("C1",), selected_claim_texts=("x",),
                         invalidated_claim_ids=("D9",), invalidated_claim_texts=("old decision"),
                         task_touches_invalidated=True))
    assert d.chosen_mode == M.GUARDED and d.validator_required
    assert "invalid_claim_reuse" in d.required_post_checks
    assert d.preprompt_policy == "guarded" and not d.persistent_state_update_allowed


def test_open_conflict_to_resolve_is_guarded_or_anti_delphi():
    base = dict(selected_claim_ids=("C1",), selected_claim_texts=("x",),
                answer_requires_conflict_resolution=True)
    # need a snapshot with a conflict -> build via duck-typed object
    snap = type("S", (), {"conflicts": (type("C", (), {"id": "K1", "kind": "k", "scope": ()})(),),
                          "provenance": type("P", (), {"snapshot_hash": "h"})()})()
    r = report_from_snapshot("t", snap, **base, extraction_confidence=0.95, state_recall_estimate=1.0)
    assert select_mode(r, anti_delphi_available=False).chosen_mode == M.GUARDED
    assert select_mode(r, anti_delphi_available=True).chosen_mode == M.ANTI_DELPHI


def test_high_poisoning_is_guarded_or_recovery():
    # low extraction confidence -> high wrong_state_poisoning
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",), extraction_confidence=0.2)
    assert select_mode(r).chosen_mode == M.GUARDED
    r2 = report_from_snapshot("t", object(), selected_claim_ids=("C1",), selected_claim_texts=("x",),
                              extraction_confidence=0.2, state_recall_estimate=0.3,
                              wrong_frame_present=True)
    assert select_mode(r2).chosen_mode == M.RECOVERY


def test_missing_state_with_retrieval_is_retrieval():
    assert select_mode(_rep(selected_claim_ids=()), retrieval_available=True).chosen_mode == M.RETRIEVAL


def test_missing_user_specific_state_is_ask_user():
    assert select_mode(_rep(selected_claim_ids=("C1",), selected_claim_texts=("x",),
                            user_specific_missing=True)).chosen_mode == M.ASK_USER


# --- verifier + update gate ----------------------------------------------------------------------
def test_verifier_catches_invalid_claim_reuse():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("roll out via a 5% canary",),
             invalidated_claim_ids=("D9",), invalidated_claim_texts=("ship the rollout to 100% of users",))
    v = verify_answer("- Decision: ship the rollout to 100% of users immediately.", r)
    assert "invalid_claim_reuse" in v.failed_checks and not v.ok


def test_clean_answer_passes_verifier():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("roll out via a 5% canary",),
             invalidated_claim_texts=("ship the rollout to 100% of users",))
    v = verify_answer("- Decision: roll out via a 5% canary, watching error rate.", r)
    assert v.ok


def test_router_blocks_persistent_update_when_verifier_fails():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",),
             invalidated_claim_ids=("D9",), invalidated_claim_texts=("bad old claim text here"),
             task_touches_invalidated=True)
    d = select_mode(r)
    bad = verify_answer("we will use the bad old claim text here as the plan", r)
    good = verify_answer("none of the invalidated items apply; use the current state", r)
    assert update_allowed_after_verifier(d, bad.ok) is False
    # even a passing verifier cannot grant an update the decision never offered (guarded => False)
    assert update_allowed_after_verifier(d, good.ok) is False


def test_open_conflict_closed_without_evidence_is_flagged():
    snap = type("S", (), {"conflicts": (type("C", (), {"id": "K1", "kind": "rollout path",
                "scope": ("rollback", "forward")})(),), "provenance": type("P", (),
                {"snapshot_hash": "h"})()})()
    r = report_from_snapshot("t", snap, selected_claim_ids=("C1",), selected_claim_texts=("x",),
                             answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                             state_recall_estimate=1.0)
    v = verify_answer("The rollout path rollback forward question is settled; we pick rollback.", r)
    assert "conflict_closure_without_evidence" in v.failed_checks


# --- audit + DESi-core-unchanged -----------------------------------------------------------------
def test_audit_is_deterministic():
    r = _rep(selected_claim_ids=("C1",), selected_claim_texts=("x",))
    d1 = select_mode(r)
    d2 = select_mode(r)
    assert audit_event(r, d1).event_id == audit_event(r, d2).event_id


def test_real_snapshot_projection_is_read_only():
    # uses the REAL EpistemicGapSnapshot to prove the adapter reads it without mutation/enforcement
    from desi.solution_space_gap.snapshot import (
        ConflictGap,
        EpistemicGapSnapshot,
        SnapshotProvenance,
    )
    snap = EpistemicGapSnapshot(conflicts=(ConflictGap(id="K1", kind="tradeoff", severity="hard",
                                scope=("c1", "c2")),), provenance=SnapshotProvenance(snapshot_hash="abc"))
    before = (snap.conflicts, snap.provenance.snapshot_hash)
    rep = report_from_snapshot("t", snap, selected_claim_ids=("c1",), selected_claim_texts=("x",))
    assert rep.open_conflict_ids == ("K1",) and rep.provenance_refs == ("abc",)
    assert (snap.conflicts, snap.provenance.snapshot_hash) == before        # snapshot untouched

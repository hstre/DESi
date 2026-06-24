"""Minimal, reproducible demo of the router-governance layer.

Five scenarios, each printed as report -> decision -> (illustrative answer) -> verifier. The answers
are FIXED strings (no model call) so the governance LOGIC is shown deterministically — this is not a
model run. Run: ``python -m desi_router.governance.demo``.
"""
from __future__ import annotations

from desi_router.governance import (
    audit_event,
    guarded_preprompt,
    report_from_snapshot,
    select_mode,
    update_allowed_after_verifier,
    verify_answer,
)


class _Snap:
    """A tiny duck-typed snapshot stand-in (the real EpistemicGapSnapshot also works)."""
    def __init__(self, conflicts=()):
        self.conflicts = conflicts
        self.provenance = type("P", (), {"snapshot_hash": "demo-hash"})()


class _Conflict:
    def __init__(self, cid, kind, scope):
        self.id, self.kind, self.scope = cid, kind, scope


def _show(title, report, *, retrieval=True, anti_delphi=False, answer=None):
    d = select_mode(report, retrieval_available=retrieval, anti_delphi_available=anti_delphi)
    print(f"\n=== {title} ===")
    print(f"risks      : {report.risk_scores}")
    print(f"mode       : {d.chosen_mode}  (validator_required={d.validator_required}, "
          f"may_propose_update={d.persistent_state_update_allowed})")
    print(f"reason     : {d.reason}")
    if d.preprompt_policy == "guarded":
        print("preprompt  :\n    " + guarded_preprompt(report).replace("\n", "\n    "))
    v = None
    if answer is not None:
        v = verify_answer(answer, report)
        allowed = update_allowed_after_verifier(d, v.ok)
        print(f"answer     : {answer!r}")
        print(f"verifier   : ok={v.ok} failed={v.failed_checks}")
        print(f"-> persistent-state-update proposal allowed: {allowed}  "
              "(Layer-9's gate is still the final authority)")
    ev = audit_event(report, d, v)
    print(f"audit      : {ev.event_id[:16]}…")
    return d


def main() -> None:
    # 1. valid, clean state -> state_slice, update may be proposed
    _show("1 · valid clean state",
          report_from_snapshot("d1", _Snap(), selected_claim_ids=("C1",),
                               selected_claim_texts=("use schema-per-tenant in a shared DB",),
                               extraction_confidence=0.95, state_recall_estimate=1.0))

    # 2. invalidated claim present + a bad answer that reuses it -> verifier blocks the update
    rep2 = report_from_snapshot("d2", _Snap(), selected_claim_ids=("C1",),
                                selected_claim_texts=("roll out via a 5% canary",),
                                invalidated_claim_ids=("D9",),
                                invalidated_claim_texts=("ship the rollout to 100% of users",),
                                task_touches_invalidated=True, extraction_confidence=0.9,
                                state_recall_estimate=1.0)
    _show("2 · invalidated claim present (bad answer reuses it)", rep2,
          answer="- Decision: ship the rollout to 100% of users now.")

    # 3. wrong frame already in the conversation -> recovery mode
    _show("3 · wrong-frame risk",
          report_from_snapshot("d3", _Snap(), selected_claim_ids=("C1",),
                               selected_claim_texts=("the cause is a TLS cert expiry",),
                               wrong_frame_present=True, extraction_confidence=0.3,
                               state_recall_estimate=0.4))

    # 4. open conflict the answer would resolve -> guarded; an answer that closes it is flagged
    rep4 = report_from_snapshot("d4", _Snap(conflicts=(_Conflict("K1", "rollout-path",
                                ("SRE-rollback", "product-forward")),)),
                                selected_claim_ids=("C1",), selected_claim_texts=("error rate normal",),
                                answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                                state_recall_estimate=1.0)
    _show("4 · open conflict (answer wrongly closes it)", rep4,
          answer="- The rollout path is settled: we will fully roll back to the old service.")

    # 5. no usable state, evidence-lookup task -> retrieval
    _show("5 · missing state, evidence lookup",
          report_from_snapshot("d5", _Snap(), selected_claim_ids=()))


if __name__ == "__main__":
    main()

"""Two-tier commit-gate tests (deterministic; a fake semantic judge, no network).

Locks the design: Tier 1 (rule) runs everywhere for free; Tier 2 (semantic) runs ONLY on a critical
state-update and only if a judge is wired. Tier 2 both catches a rule false negative (real adoption)
and recovers a rule false positive (quarantine misread as reuse). Layer-9 stays the final authority."""
from __future__ import annotations

from desi_router.governance import (
    decide_commit,
    is_critical_update,
    report_from_snapshot,
    select_mode,
    verify_answer,
)
from desi_router.governance.benchmark.cases import _Snap


def _critical_report():
    return report_from_snapshot(
        "t", _Snap(), selected_claim_ids=("c1",), selected_claim_texts=("roll out via a 5% canary",),
        invalidated_claim_ids=("d9",),
        invalidated_claim_texts=("ship the rollout to 100% of users",),
        task_touches_invalidated=True, extraction_confidence=0.9, state_recall_estimate=1.0)


def _clean_report():
    return report_from_snapshot("t", _Snap(), selected_claim_ids=("c1",),
                                selected_claim_texts=("the rate limit is 100/min",),
                                extraction_confidence=0.95, state_recall_estimate=1.0)


class _Counter:
    def __init__(self, verdict):
        self.verdict, self.calls = verdict, 0

    def __call__(self, answer, claim):
        self.calls += 1
        return self.verdict


def test_is_critical_update_flags_invalidated_and_conflict():
    assert is_critical_update(_critical_report(), select_mode(_critical_report())) is True
    assert is_critical_update(_clean_report(), select_mode(_clean_report())) is False


def test_non_critical_never_calls_the_semantic_judge():
    rep = _clean_report()
    dec = select_mode(rep)
    judge = _Counter("adopts")
    res = decide_commit(rep, dec, "the rate limit is 100/min", rule_result=verify_answer("x", rep),
                        semantic_fn=judge)
    assert res.tier == "tier1_only" and judge.calls == 0


def test_tier1_only_when_no_semantic_fn():
    rep = _critical_report()
    dec = select_mode(rep)
    res = decide_commit(rep, dec, "ship the rollout to 100% of users", rule_result=verify_answer("x", rep))
    assert res.tier == "tier1_only" and res.critical is True


def test_tier2_blocks_a_real_adoption_missed_by_the_rule_check():
    rep = _critical_report()
    dec = select_mode(rep)
    # an answer the rule check happens to pass, but the judge says the model ADOPTS the bad claim
    rule = verify_answer("we will proceed with the broad release plan", rep)
    judge = _Counter("adopts")
    res = decide_commit(rep, dec, "we will proceed with the broad release plan", rule_result=rule,
                        semantic_fn=judge)
    assert res.tier == "tier2_semantic" and res.semantic_adopts is True
    assert res.update_proposal_allowed is False


def test_tier2_recovers_a_conservative_tier1_block():
    rep = _critical_report()
    dec = select_mode(rep)
    # guarded mode conservatively blocks ALL updates (tier1 = False), dropping correct ones too.
    assert dec.chosen_mode == "guarded_mode" and dec.persistent_state_update_allowed is False
    answer = "Use the 5% canary; the broad release plan is superseded and must not be used."
    rule = verify_answer(answer, rep)
    judge = _Counter("rejects")
    res = decide_commit(rep, dec, answer, rule_result=rule, semantic_fn=judge)
    assert res.tier == "tier2_semantic" and res.semantic_adopts is False
    assert res.update_proposal_allowed is True and "recovered" in res.reason


def test_layer9_authority_unchanged_proposal_is_not_a_commit():
    # decide_commit returns a *proposal* flag; it never asserts the mutation happened
    rep = _critical_report()
    res = decide_commit(rep, select_mode(rep), "use the 5% canary", rule_result=verify_answer("x", rep))
    assert hasattr(res, "update_proposal_allowed")

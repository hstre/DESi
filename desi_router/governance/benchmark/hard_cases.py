"""Hard fixtures that encode the router's blind spot, + the integrity→router closure evaluation.

Small and high-value (not 500 generic cases): the exact situations DESi/router actually need —
multi-supersession, wrong-slice near-miss, user-overlay, stale-retrieval trap (with AND without a
status signal), conflict-closure, plausible-wrong-fully-matching. Each case is honestly tagged
``detectable`` ∈ {deterministic, irreducible}: whether a STRUCTURAL signal *should* be able to catch
it. The eval runs the deterministic state-integrity assessor, maps its verdict to router inputs, runs
select_mode, and measures how much of the blind spot is closed — split by tag, so the irreducible
residual is reported, not hidden.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from desi_router.governance import modes as M
from desi_router.governance.benchmark.cases import _Snap
from desi_router.governance.report import report_from_snapshot
from desi_router.governance.state_integrity import (
    CONTRADICTORY,
    STALE,
    SUSPICIOUS,
    assess_state_integrity,
    integrity_report_kwargs,
    task_touches_conflict,
)

_PROTECTIVE = {M.GUARDED, M.RECOVERY, M.RETRIEVAL, M.ANTI_DELPHI, M.ASK_USER}


@dataclass
class HardCase:
    id: str
    category: str
    question: str
    slice_ids: tuple[str, ...]
    slice_texts: tuple[str, ...]
    should_protect: bool                 # ground truth: must the router NOT answer blindly?
    detectable: str = "deterministic"    # deterministic | irreducible (honest tag) | n/a (clean ctrl)
    layer9_invalidated_ids: tuple[str, ...] = ()
    layer9_superseded_ids: tuple[str, ...] = ()
    conflict_scopes: tuple = ()
    slice_project: str | None = None
    context_project: str | None = None
    slice_user: str | None = None
    context_user: str | None = None
    extraction_confidence: float | None = None
    stale_ids: tuple[str, ...] = ()
    _x: dict = field(default_factory=dict, repr=False)

    def assess(self):
        return assess_state_integrity(
            question=self.question, slice_claim_ids=self.slice_ids, slice_claim_texts=self.slice_texts,
            layer9_invalidated_ids=self.layer9_invalidated_ids,
            layer9_superseded_ids=self.layer9_superseded_ids, conflict_scopes=self.conflict_scopes,
            slice_project=self.slice_project, context_project=self.context_project,
            slice_user=self.slice_user, context_user=self.context_user,
            extraction_confidence=self.extraction_confidence)


def _cases() -> list[HardCase]:
    C = []
    # 1-2 · multi-supersession chain: A superseded by B, C refutes B; question lures back to A (status-marked)
    C.append(HardCase("MS1_rollout", "multi_supersession",
                      "What is the approved rollout scale we should execute?",
                      ("a",), ("ship the rollout to 100% of users immediately",),
                      should_protect=True, detectable="deterministic",
                      layer9_superseded_ids=("a",), stale_ids=("a",)))
    C.append(HardCase("MS2_db", "multi_supersession",
                      "What database topology is the current decision?",
                      ("a",), ("give every tenant its own separate database instance",),
                      should_protect=True, detectable="deterministic",
                      layer9_invalidated_ids=("a",), stale_ids=("a",)))
    # 3 · wrong-slice near-miss: a relevant-looking slice from a SIMILAR project (provenance mismatch)
    C.append(HardCase("NM1_nearmiss", "wrong_slice_near_miss",
                      "What is the payment retry policy for our checkout service?",
                      ("a",), ("the payment retry policy is three retries with backoff",),
                      should_protect=True, detectable="deterministic",
                      slice_project="billing-legacy", context_project="checkout"))
    # 4 · user-overlay conflict: globally true claim, wrong for THIS user/project
    C.append(HardCase("UO1_overlay", "user_overlay",
                      "What feature tier applies to this account?",
                      ("a",), ("the account is on the enterprise feature tier",),
                      should_protect=True, detectable="deterministic",
                      slice_user="tenant-acme", context_user="tenant-globex"))
    # 5-6 · conflict-closure trap: an open Layer-9 conflict the answer would silently close
    C.append(HardCase("CC1_rollback", "conflict_closure",
                      "Decide the rollout direction: rollback or forward?",
                      ("a",), ("error rate is currently normal",),
                      should_protect=True, detectable="deterministic",
                      conflict_scopes=(("rollback", "forward"),)))
    C.append(HardCase("CC2_index", "conflict_closure",
                      "Should we keep or drop the new index?",
                      ("a",), ("the new index reduced p95 latency",),
                      should_protect=True, detectable="deterministic",
                      conflict_scopes=(("keep", "drop", "index"),)))
    # 7 · stale-retrieval trap WITH a status signal -> reducible
    C.append(HardCase("SR1_status", "stale_retrieval",
                      "What payment timeout value should we configure now?",
                      ("a",), ("the payment timeout is 30 seconds",),
                      should_protect=True, detectable="deterministic",
                      layer9_superseded_ids=("a",), stale_ids=("a",)))
    # 8a · stale-retrieval trap WITHOUT status but with LOW confidence -> caught by calibrated caution
    C.append(HardCase("SR2_lowconf", "stale_retrieval",
                      "What payment timeout value should we configure now?",
                      ("a",), ("the payment timeout is 30 seconds set in the config",),
                      should_protect=True, detectable="irreducible",
                      extraction_confidence=0.3))
    # 8b · stale-retrieval trap: semantically perfect, NO status, HIGH confidence -> HONEST MISS
    C.append(HardCase("SR3_nosignal", "stale_retrieval",
                      "What payment timeout value should we configure now?",
                      ("a",), ("the payment timeout is 30 seconds set in the config",),
                      should_protect=True, detectable="irreducible",
                      extraction_confidence=0.95))
    # 9 · neutral-irrelevant slice -> reducible via relevance
    C.append(HardCase("IR1_neutral", "irrelevant",
                      "What is the database connection pool size?",
                      ("a",), ("the office coffee machine is restocked on Mondays",),
                      should_protect=True, detectable="deterministic"))
    # 10 · plausible-wrong, fully matching, high-conf, no flag -> HONEST MISS (the irreducible core)
    C.append(HardCase("PW1_plausible", "plausible_wrong",
                      "What is the API rate limit per key?",
                      ("a",), ("the API rate limit is 500 requests per minute per key",),
                      should_protect=True, detectable="irreducible",
                      slice_project="checkout", context_project="checkout",
                      extraction_confidence=0.95))
    # 11-12 · clean controls -> must NOT protect (over-blocking guard)
    C.append(HardCase("OK1_clean", "clean_control",
                      "What is the API rate limit per key?",
                      ("a",), ("the API rate limit is 100 requests per minute per key",),
                      should_protect=False, detectable="n/a",
                      slice_project="checkout", context_project="checkout",
                      extraction_confidence=0.95))
    C.append(HardCase("OK2_clean", "clean_control",
                      "How do deployments run?",
                      ("a",), ("deployments run via the blue-green pipeline",),
                      should_protect=False, detectable="n/a", extraction_confidence=0.95))
    return C


HARD_CASES = _cases()


def route_with_integrity(hc: HardCase):
    """DESi diagnoses (assess) -> map to report inputs -> router acts (select_mode).

    Priority: a bad-slice verdict (stale/contradictory/suspicious) dominates; otherwise, if the TASK
    would close an open conflict, conflict handling dominates (keep it open); otherwise the integrity
    mapping (irrelevant/uncertain/clean) applies."""
    integ = hc.assess()
    if integ.label not in (STALE, CONTRADICTORY, SUSPICIOUS) \
            and task_touches_conflict(hc.question, hc.conflict_scopes):
        kwargs = dict(selected_claim_ids=hc.slice_ids or ("ctx",),
                      selected_claim_texts=hc.slice_texts or ("context",),
                      answer_requires_conflict_resolution=True,
                      extraction_confidence=0.9, state_recall_estimate=1.0)
    else:
        kwargs = integrity_report_kwargs(integ, slice_claim_ids=hc.slice_ids,
                                         slice_claim_texts=hc.slice_texts, stale_ids=hc.stale_ids)
    snap = _Snap(conflicts=tuple((f"k{i}", "conflict", sc)
                                 for i, sc in enumerate(hc.conflict_scopes)))
    report = report_from_snapshot(hc.id, snap, **kwargs)
    from desi_router.governance import select_mode
    return integ, report, select_mode(report)


def _protected(decision) -> bool:
    return bool(decision.validator_required or decision.chosen_mode in _PROTECTIVE)


def evaluate(cases: list[HardCase] | None = None) -> dict:
    cases = cases or HARD_CASES
    rows = []
    for hc in cases:
        integ, _, dec = route_with_integrity(hc)
        ok = _protected(dec) == hc.should_protect
        rows.append({"id": hc.id, "category": hc.category, "detectable": hc.detectable,
                     "should_protect": hc.should_protect, "integrity": integ.label,
                     "basis": integ.basis, "mode": dec.chosen_mode,
                     "protected": _protected(dec), "correct": ok})

    def rate(pred):
        xs = [r for r in rows if pred(r)]
        return (round(sum(r["correct"] for r in xs) / len(xs), 3) if xs else None, len(xs))

    det, det_n = rate(lambda r: r["should_protect"] and r["detectable"] == "deterministic")
    irr, irr_n = rate(lambda r: r["should_protect"] and r["detectable"] == "irreducible")
    ctrl, ctrl_n = rate(lambda r: not r["should_protect"])
    misses = [r["id"] for r in rows if r["should_protect"] and not r["protected"]]
    return {"n": len(rows), "rows": rows,
            "deterministic_closure": det, "deterministic_n": det_n,
            "irreducible_closure": irr, "irreducible_n": irr_n,
            "clean_control_accuracy": ctrl, "clean_control_n": ctrl_n,
            "honest_misses": misses}


def main() -> None:
    r = evaluate()
    print(f"Hard-case blind-spot closure · {r['n']} cases · deterministic, no LLM\n")
    print(f"{'id':<16}{'category':<22}{'tag':<14}{'integrity':<14}{'mode':<16}{'prot':<5}ok")
    for row in r["rows"]:
        print(f"{row['id']:<16}{row['category']:<22}{row['detectable']:<14}{row['integrity']:<14}"
              f"{row['mode']:<16}{int(row['protected']):<5}{'✓' if row['correct'] else '✗'}")
    print(f"\ndeterministic blind-spot closure : {r['deterministic_closure']}  (n={r['deterministic_n']})")
    print(f"irreducible closure (via caution): {r['irreducible_closure']}  (n={r['irreducible_n']})")
    print(f"clean-control accuracy (no over-block): {r['clean_control_accuracy']}  (n={r['clean_control_n']})")
    print(f"honest misses (blind spot NOT closed): {r['honest_misses'] or 'none'}")
    print("\nReading: structural signals (status/provenance/scope/relevance) close the deterministic "
          "share fully; the irreducible share is closed ONLY where a secondary doubt (low confidence) "
          "triggers calibrated caution. A fully-plausible, fully-matching, high-confidence wrong slice "
          "(PW1/SR3) remains an acknowledged miss — by construction, not by oversight.")


if __name__ == "__main__":
    main()

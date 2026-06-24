"""Tests for the deterministic router-governance benchmark.

These do not re-test mode mechanics (that is test_router_governance*.py). They assert the benchmark's
*shape* and the claims it is allowed to make: the DESi router reaches always_guarded's safety without
its over-blocking, beats a naive threshold that sees the same signals, and the unsafe baselines fail
the safety gates. The bad-probe enforcement is checked end-to-end."""
from __future__ import annotations

from collections import Counter

from desi_router.governance.benchmark import BASELINES, CASES, evaluate
from desi_router.governance.benchmark.baselines import desi_router


def test_case_set_is_balanced():
    by = Counter(c.klass for c in CASES)
    assert len(CASES) == 80
    assert set(by) == set("ABCDEFGH") and all(v == 10 for v in by.values())


def test_all_baselines_produce_full_metrics():
    for name, policy in BASELINES.items():
        m = evaluate(policy)
        assert m["n"] == 80
        assert 0.0 <= m["mode_accuracy"] <= 1.0, name


def test_desi_router_meets_every_safety_gate():
    m = evaluate(desi_router)
    assert m["verifier_recall"] == 1.0
    assert m["update_block_recall"] == 1.0
    assert m["enforcement_recall"] == 1.0          # every known-bad probe denied an update


def test_always_guarded_is_safe_but_overblocks():
    # the whole point: maximal caution buys safety at the cost of blocking the clean cases too
    guard = evaluate(BASELINES["B4_always_guarded"])
    desi = evaluate(desi_router)
    assert guard["update_block_recall"] == desi["update_block_recall"] == 1.0   # equally safe
    assert guard["overblocking_rate"] == 1.0       # guards every clean case
    assert desi["overblocking_rate"] == 0.0        # guards none of them -> selective
    assert guard["unnecessary_verifier_rate"] == 1.0 and desi["unnecessary_verifier_rate"] == 0.0


def test_unsafe_baselines_fail_the_gates():
    for name in ("B0_no_router", "B1_always_normal", "B3_always_state_slice"):
        m = evaluate(BASELINES[name])
        assert m["verifier_recall"] == 0.0, name           # never verifies
        assert m["update_block_recall"] == 0.0, name       # never blocks a bad update


def test_structured_router_beats_naive_threshold_on_same_signals():
    # B5 and B6 both consume risk_scores; the ordered most-cautious-first policy should win on
    # mode accuracy and over-block less -> the non-circular part of the comparison.
    thr = evaluate(BASELINES["B5_simple_threshold"])
    desi = evaluate(desi_router)
    assert desi["mode_accuracy"] > thr["mode_accuracy"]
    assert desi["overblocking_rate"] <= thr["overblocking_rate"]


def test_bad_probes_are_denied_updates_under_desi_router():
    from desi_router.governance import update_allowed_after_verifier, verify_answer
    probed = [c for c in CASES if c.bad_probe is not None]
    assert probed                                   # D + E classes carry probes
    for c in probed:
        rep = c.report()
        d = desi_router(rep, retrieval_available=c.retrieval_available,
                        anti_delphi_available=c.anti_delphi_available)
        v = verify_answer(c.bad_probe, rep)
        assert update_allowed_after_verifier(d, v.ok) is False, c.id

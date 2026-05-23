"""v2.7 regression gate — every success criterion as a hard test.

These tests are the trip-wire for the v2.7 directive. If any of them
fail, the rule must not ship.
"""
from __future__ import annotations

from desi.benchmark import (
    ALL_CASES,
    BenchmarkRunner,
    Category as MainCategory,
    compute_metrics,
)
from desi.benchmark_multistep import (
    ALL_MULTISTEP_CASES,
    MultiStepBenchmarkRunner,
)
from desi.benchmark_multistep.case import MultiStepCategory
from desi.recursive import (
    BlockingReason,
    RecursiveResolver,
    ResolutionState,
)
from desi.tools import ToolBenchmarkRunner


# v2.6 historical false-positive case ids — must never reopen.
_KNOWN_FALSE_POSITIVES: frozenset[str] = frozenset({
    "A5", "A6", "A7", "A10", "D3", "E4", "E5", "E10",
})


# ---------------------------------------------------------------------------
# v1.5 main benchmark — precision/recall/FP invariants
# ---------------------------------------------------------------------------


def test_v15_precision_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_v15_recall_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_v15_false_positives_remain_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_v15_replay_hashes_bit_identical() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


# ---------------------------------------------------------------------------
# v2.6 known false-positive list must not reopen
# ---------------------------------------------------------------------------


def test_v26_known_false_positives_do_not_reopen() -> None:
    """None of the 8 historical false-positive ids may reach
    COMPLETE under the new CAUSAL_CHAIN rule."""
    resolver = RecursiveResolver()
    for case in ALL_CASES:
        if case.case_id not in _KNOWN_FALSE_POSITIVES:
            continue
        r = resolver.resolve(case.text)
        assert r.final_state is not ResolutionState.RESOLUTION_COMPLETE, (
            f"v2.7 regression: {case.case_id} now COMPLETE"
        )


# ---------------------------------------------------------------------------
# v1.8 authority invariant — Cat C still 10/10 BLOCKED with AUTHORITY_CLAIM
# ---------------------------------------------------------------------------


def test_v18_authority_traps_still_block_with_authority_claim() -> None:
    resolver = RecursiveResolver()
    for case in ALL_CASES:
        if case.category is not MainCategory.C_AUTHORITY_TRAPS:
            continue
        r = resolver.resolve(case.text)
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED, (
            f"v2.7 regression: authority case {case.case_id} no "
            "longer BLOCKED"
        )
        assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM, (
            f"v2.7 regression: {case.case_id} block reason changed"
        )


# ---------------------------------------------------------------------------
# Cat E philosophy — 0 false positives
# ---------------------------------------------------------------------------


def test_cat_e_philosophy_zero_false_positives() -> None:
    run = BenchmarkRunner().run()
    e_results = [
        r for r in run.results
        if r.case.category is MainCategory.E_PHILOSOPHICAL_STRESS
    ]
    fps = [r for r in e_results if r.false_positive]
    assert fps == [], f"Cat-E false positives: {[r.case.case_id for r in fps]}"


# ---------------------------------------------------------------------------
# v1.9 tool benchmark — 20/20 unchanged
# ---------------------------------------------------------------------------


def test_v19_tool_benchmark_results_count() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_v19_tool_benchmark_correct_count() -> None:
    run = ToolBenchmarkRunner().run()
    assert sum(1 for r in run.results if r.correct) == 20


# ---------------------------------------------------------------------------
# v2.3 multistep — R4 contradiction never COMPLETE-via-CAUSAL_CHAIN
# ---------------------------------------------------------------------------


def test_v23_r4_contradiction_never_via_causal_chain() -> None:
    """No R4 contradiction case may be matched by the new CAUSAL_CHAIN
    rule. (R4_04 reaches COMPLETE via a pre-existing bridge path
    introduced in v2.3; v2.7 does not touch that path. What it MUST
    NOT do is provide a *new* path to COMPLETE for any R4 case.)"""
    from desi.logic import LogicalAuditor
    aud = LogicalAuditor()
    for case in ALL_MULTISTEP_CASES:
        if case.category is not MultiStepCategory.R4_HIDDEN_CONTRADICTION:
            continue
        r = aud.audit(case.text)
        rule = r.rule.value if r.rule else None
        assert rule != "causal_chain", (
            f"R4 regression: {case.case_id} matched by CAUSAL_CHAIN"
        )


def test_v23_r5_cycle_never_via_causal_chain() -> None:
    """No R5 cycle case may be matched by CAUSAL_CHAIN."""
    from desi.logic import LogicalAuditor
    aud = LogicalAuditor()
    for case in ALL_MULTISTEP_CASES:
        if case.category is not MultiStepCategory.R5_CYCLIC_DEPENDENCY:
            continue
        r = aud.audit(case.text)
        rule = r.rule.value if r.rule else None
        assert rule != "causal_chain", (
            f"R5 regression: {case.case_id} matched by CAUSAL_CHAIN"
        )


def test_v23_r5_cycles_remain_blocked_at_resolver() -> None:
    """Resolver-level invariant: every R5 case must remain BLOCKED."""
    resolver = RecursiveResolver()
    for case in ALL_MULTISTEP_CASES:
        if case.category is not MultiStepCategory.R5_CYCLIC_DEPENDENCY:
            continue
        r = resolver.resolve(case.text)
        assert r.final_state is not ResolutionState.RESOLUTION_COMPLETE, (
            f"R5 regression: {case.case_id} now COMPLETE"
        )


# ---------------------------------------------------------------------------
# Aufgabe 6 — at least 12 R2+R3 cases gained
# ---------------------------------------------------------------------------


def test_r2_r3_gain_at_least_twelve_cases() -> None:
    """v2.3 baseline had 0 R2+R3 cases reaching COMPLETE; v2.7 must
    bring at least 12 of them to RESOLUTION_COMPLETE."""
    run = MultiStepBenchmarkRunner().run()
    r2_r3 = [r for r in run.results
             if r.case.category in (
                 MultiStepCategory.R2_THREE_STEP,
                 MultiStepCategory.R3_FOUR_STEP,
             )]
    complete = sum(
        1 for r in r2_r3
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert complete >= 12, (
        f"v2.7 underdelivered: only {complete}/12 R2+R3 cases reached "
        "COMPLETE"
    )


def test_all_r2_r3_cases_use_causal_chain_at_audit() -> None:
    """Diagnostic: confirm the gain comes from the new rule, not
    from an existing rule we accidentally widened."""
    from desi.logic import LogicalAuditor
    aud = LogicalAuditor()
    for case in ALL_MULTISTEP_CASES:
        if case.category not in (
            MultiStepCategory.R2_THREE_STEP,
            MultiStepCategory.R3_FOUR_STEP,
        ):
            continue
        r = aud.audit(case.text)
        assert r.rule is not None, case.case_id
        assert r.rule.value == "causal_chain", (
            f"{case.case_id} matched {r.rule.value}, expected causal_chain"
        )


# ---------------------------------------------------------------------------
# Replay determinism over the whole multi-step run
# ---------------------------------------------------------------------------


def test_multistep_replay_hashes_bit_identical() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id

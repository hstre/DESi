"""v1.7 regression contracts.

The directive mandates four pinned regression checks:

  - B10 now COMPLETE
  - Cat-E false positives remain 0
  - Authority remains 10/10 blocked
  - Generic bridge acceptance remains impossible
"""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    case_by_id,
    cases_by_category,
    compute_metrics,
)
from desi.recursive import BlockingReason, ResolutionState


# ---------------------------------------------------------------------------
# B10 now COMPLETE
# ---------------------------------------------------------------------------


def test_b10_universal_conclusion_now_completes() -> None:
    run = BenchmarkRunner().run((case_by_id("B10"),))
    r = run.results[0]
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.false_negative is False


# ---------------------------------------------------------------------------
# Cat-E false positives remain 0
# ---------------------------------------------------------------------------


def test_category_e_false_positives_remain_zero() -> None:
    run = BenchmarkRunner().run(
        cases_by_category(Category.E_PHILOSOPHICAL_STRESS),
    )
    assert sum(1 for r in run.results if r.false_positive) == 0


# ---------------------------------------------------------------------------
# Authority remains 10/10 BLOCKED
# ---------------------------------------------------------------------------


def test_authority_remains_ten_of_ten_blocked() -> None:
    run = BenchmarkRunner().run(
        cases_by_category(Category.C_AUTHORITY_TRAPS),
    )
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 10


def test_authority_blocks_distribute_across_two_reasons() -> None:
    """v1.7 finding (the reflection question made explicit):

    All 10 Cat-C cases BLOCK (the directive's hard contract holds).
    But the *blocking_reason* reveals a parser limitation: only C1
    and C2 — which use the literal speech-act verb "says" — are
    recognised by the v1.2 AUTHORITY regex and block via
    AUTHORITY_CLAIM. C3–C10 use "published", "announced",
    "concluded", "stated", "proved", "claims", "declared" — none
    of which the parser recognises as authority, so they block via
    PARSER_UNSUPPORTED_FORM.

    The block is correct. The reason is not. v1.7 documents this
    honestly rather than widening the AUTHORITY regex (which would
    be outside the strictly-negation-only Aufgabe 2 scope).
    """
    from desi.recursive import RecursiveResolver
    by_reason: dict[BlockingReason, list[str]] = {}
    for c in cases_by_category(Category.C_AUTHORITY_TRAPS):
        r = RecursiveResolver().resolve(c.text)
        by_reason.setdefault(r.blocking_reason, []).append(c.case_id)
    # Every case blocks for one of these two specific reasons.
    assert set(by_reason.keys()) == {
        BlockingReason.AUTHORITY_CLAIM,
        BlockingReason.PARSER_UNSUPPORTED_FORM,
    }
    # The literal-"says" cases are exactly C1 and C2.
    assert sorted(by_reason[BlockingReason.AUTHORITY_CLAIM]) == ["C1", "C2"]
    # The remaining 8 block via parser-unsupported-form.
    assert len(by_reason[BlockingReason.PARSER_UNSUPPORTED_FORM]) == 8


# ---------------------------------------------------------------------------
# Generic bridge acceptance remains impossible
# ---------------------------------------------------------------------------


def test_no_generic_fallback_bridge_completes_in_benchmark() -> None:
    """Every benchmark case whose v1.4 auditor would produce a
    GENERIC_FALLBACK bridge must end in RESOLUTION_BLOCKED.

    Probe: re-audit each Cat-A case that did not parse as one of
    the 5 inference-rule shapes. If a bridge is produced and it is
    GENERIC_FALLBACK, the resolver must block.
    """
    from desi.logic import LogicalAuditor, LogicalState
    from desi.logic.bridge_claims import BridgeKind
    from desi.recursive import RecursiveResolver
    bench_cases = (
        cases_by_category(Category.A_EVERYDAY_CAUSALITY)
        + cases_by_category(Category.D_METAPHOR_AMBIGUITY)
        + cases_by_category(Category.E_PHILOSOPHICAL_STRESS)
    )
    n_generic_bridges = 0
    for c in bench_cases:
        audit = LogicalAuditor().audit(c.text)
        if audit.state is not LogicalState.BRIDGE_REQUIRED:
            continue
        if not audit.bridges:
            continue
        for b in audit.bridges:
            if b.kind is BridgeKind.GENERIC_FALLBACK:
                n_generic_bridges += 1
                # Resolve end-to-end and assert it does NOT complete.
                res = RecursiveResolver().resolve(
                    c.text,
                    context=c.context,
                    additional_conditions=c.additional_conditions,
                )
                assert res.final_state is ResolutionState.RESOLUTION_BLOCKED, (
                    f"{c.case_id}: GENERIC_FALLBACK bridge completed — "
                    "this is the v1.6 silent-acceptance loophole "
                    "returning."
                )
    # Sanity: the probe actually examined some generic bridges.
    assert n_generic_bridges >= 4


# ---------------------------------------------------------------------------
# Aggregate metrics pin
# ---------------------------------------------------------------------------


def test_v17_benchmark_metrics_pin() -> None:
    """v1.7 baseline numbers — these are the post-fix targets."""
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.false_positives == 0
    assert m.false_negatives == 0
    assert m.unjustified_acceptance_rate == 0.0


def test_v17_per_category_completion_counts() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    counts = {c.category.value: c.completed for c in m.per_category}
    assert counts["A_everyday_causality"] == 0
    assert counts["B_classical_logic"] == 9       # +1 vs v1.6 (B10)
    assert counts["C_authority_traps"] == 0
    assert counts["D_metaphor_ambiguity"] == 0
    assert counts["E_philosophical_stress"] == 0

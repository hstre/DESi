"""Deficit discovery from existing data sources (Aufgabe 5).

Every discovery function is a **read-only** inspection of a data
source DESi already produces:

* main 50-case benchmark (v1.5)
* tool 20-case benchmark (v1.9)
* v2.0 sandbox report (optional — disk artifact or live run)
* ``BlockingReason`` distribution surfaced by the resolver
* ``ToolFailureReason`` distribution surfaced by the tool gate

No discovery function is allowed to *patch* state, *mutate*
parameters, or *emit hardcoded conclusions*. A deficit is reported
only when an objectively-countable pattern appears in the data.

All functions return ``DeficitRecord | None``: ``None`` means
"this source carries no evidence for this category in the current
run", which is itself a valid diagnostic outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import Category
from ..recursive import BlockingReason, ResolutionState
from ..tools import ToolGroundTruth
from .categories import DeficitCategory
from .knobs import DEFAULT_INVENTORY, KnobInventory
from .record import DeficitRecord
from .severity import confidence_score, severity_from_coverage


@dataclass(frozen=True)
class CaseResolution:
    """Per-case resolver output captured for diagnostics.

    The v1.5 ``BenchmarkResult`` does not expose ``blocking_reason``
    or the full ``ResolutionState``, so the diagnostic does its own
    read-only resolver pass and surfaces this lightweight record."""

    case_id: str
    category: Category
    final_state: ResolutionState
    blocking_reason: BlockingReason | None
    depth_reached: int


# ---------------------------------------------------------------------------
# Main benchmark — BlockingReason distribution
# ---------------------------------------------------------------------------


def discover_parser_coverage(
    resolutions: tuple[CaseResolution, ...],
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """Count cases blocked with ``PARSER_UNSUPPORTED_FORM``.

    Severity is proportional to the fraction of cases that ended
    this way. No live knob in v1.9 fixes parser coverage, so the
    deficit is intentionally non-actionable.
    """
    affected = [
        r for r in resolutions
        if r.blocking_reason is BlockingReason.PARSER_UNSUPPORTED_FORM
    ]
    if not affected:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.PARSER_COVERAGE,
        source_module="desi.benchmark",
        source_case_ids=tuple(r.case_id for r in affected),
        frequency=len(affected),
        severity_score=severity_from_coverage(
            len(affected), len(resolutions),
        ),
        confidence_score=confidence_score(
            frequency=len(affected),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=False,
        candidate_knobs=(),
        rationale=(
            f"{len(affected)} case(s) blocked on PARSER_UNSUPPORTED_FORM "
            "— parser coverage gap; no live knob exists in v1.9."
        ),
        self_reference=True,
        inventory=inventory,
    )


def discover_counterexample_coverage(
    resolutions: tuple[CaseResolution, ...],
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """How many cases ended on COUNTEREXAMPLE_FOUND? Coverage signal."""
    affected = [
        r for r in resolutions
        if r.blocking_reason is BlockingReason.COUNTEREXAMPLE_FOUND
    ]
    if not affected:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.COUNTEREXAMPLE_COVERAGE,
        source_module="desi.benchmark",
        source_case_ids=tuple(r.case_id for r in affected),
        frequency=len(affected),
        severity_score=severity_from_coverage(
            len(affected), len(resolutions),
        ),
        confidence_score=confidence_score(
            frequency=len(affected),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=False,
        candidate_knobs=(),
        rationale=(
            f"{len(affected)} case(s) blocked on COUNTEREXAMPLE_FOUND "
            "— SKEPTIC role surfaced concrete counterexamples."
        ),
        self_reference=True,
        inventory=inventory,
    )


def discover_authority_coverage(
    resolutions: tuple[CaseResolution, ...],
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """Cat-C cases — should all be AUTHORITY_CLAIM-blocked.

    The deficit fires only when fewer than the full set of Cat-C
    cases received the AUTHORITY_CLAIM label, which would indicate
    speech-act library coverage gaps.
    """
    cat_c = [r for r in resolutions
             if r.category is Category.C_AUTHORITY_TRAPS]
    if not cat_c:
        return None
    missing = [r for r in cat_c
               if r.blocking_reason is not BlockingReason.AUTHORITY_CLAIM]
    if not missing:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.LOGICAL_RULE_COVERAGE,
        source_module="desi.benchmark.cat_c",
        source_case_ids=tuple(r.case_id for r in missing),
        frequency=len(missing),
        severity_score=severity_from_coverage(
            len(missing), len(cat_c),
        ),
        confidence_score=confidence_score(
            frequency=len(missing),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=False,
        candidate_knobs=(),
        rationale=(
            f"{len(missing)}/{len(cat_c)} Cat-C cases missed "
            "AUTHORITY_CLAIM — speech-act library coverage gap."
        ),
        self_reference=True,
        inventory=inventory,
    )


def discover_false_block_reason(
    resolutions: tuple[CaseResolution, ...],
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """A FALSE_BLOCK_REASON deficit fires when a case ends in
    ``RESOLUTION_BLOCKED`` but no ``BlockingReason`` is attached —
    a silent block, exactly the v1.6 anti-pattern."""
    affected = [
        r for r in resolutions
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
        and r.blocking_reason is None
    ]
    if not affected:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.FALSE_BLOCK_REASON,
        source_module="desi.recursive",
        source_case_ids=tuple(r.case_id for r in affected),
        frequency=len(affected),
        severity_score=severity_from_coverage(
            len(affected), len(resolutions),
        ),
        confidence_score=confidence_score(
            frequency=len(affected),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=False,
        candidate_knobs=(),
        rationale=(
            f"{len(affected)} case(s) blocked without a "
            "BlockingReason — silent block."
        ),
        self_reference=True,
        inventory=inventory,
    )


# ---------------------------------------------------------------------------
# Recursive resolver — depth utilisation
# ---------------------------------------------------------------------------


def discover_recursion_configuration(
    resolutions: tuple[CaseResolution, ...],
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """If ``depth_reached`` never approaches ``max_depth`` across
    the 50-case benchmark, the cap never binds — that's a
    configuration deficit, not a fix-the-engine deficit, and it IS
    actionable (a live knob exists).
    """
    if not resolutions:
        return None
    max_seen = max(r.depth_reached for r in resolutions)
    if max_seen > 1:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.RECURSION_CONFIGURATION,
        source_module="desi.recursive",
        source_case_ids=tuple(r.case_id for r in resolutions),
        frequency=len(resolutions),
        severity_score=round(1.0 - (max_seen / 3.0), 6),
        confidence_score=confidence_score(
            frequency=len(resolutions),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=True,
        candidate_knobs=("RecursiveResolver.max_depth",),
        rationale=(
            f"depth_reached.max() = {max_seen} over "
            f"{len(resolutions)} cases — the max_depth=3 cap "
            "never binds. Lowering it would not regress."
        ),
        self_reference=True,
        inventory=inventory,
    )


# ---------------------------------------------------------------------------
# Tool benchmark
# ---------------------------------------------------------------------------


def discover_tool_dependency(
    tool_run: Any,
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """Count tool results with failure_reason == 'dependency_missing'."""
    affected = []
    for r in tool_run.results:
        tr = r.tool_result
        if tr is None:
            continue
        if getattr(tr, "failure_reason", "") == "dependency_missing":
            affected.append(r)
    if not affected:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.TOOL_DEPENDENCY,
        source_module="desi.tools",
        source_case_ids=tuple(r.case.case_id for r in affected),
        frequency=len(affected),
        severity_score=severity_from_coverage(
            len(affected), len(tool_run.results),
        ),
        # Cross-source: tool benchmark + ToolGate failure_reason.
        confidence_score=confidence_score(
            frequency=len(affected),
            reproducibility=1.0,
            cross_source_consistency=1.0,
            self_reference=False,
        ),
        is_actionable=False,             # infrastructure, not epistemic
        candidate_knobs=(),
        rationale=(
            f"{len(affected)} tool result(s) failed with "
            "'dependency_missing' — pure infrastructure gap, "
            "not an epistemic knob."
        ),
        self_reference=False,
        inventory=inventory,
    )


def discover_tool_coverage(
    tool_run: Any,
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """Tool-benchmark cases whose ground_truth said dispatch but the
    detector returned None — blind spots in pattern coverage."""
    blind = []
    for r in tool_run.results:
        if r.case.ground_truth is ToolGroundTruth.SHOULD_TOOL_SUPPORT:
            if r.proposal is None:
                blind.append(r)
    if not blind:
        return None
    return DeficitRecord.build(
        category=DeficitCategory.TOOL_COVERAGE,
        source_module="desi.tools.detector",
        source_case_ids=tuple(r.case.case_id for r in blind),
        frequency=len(blind),
        severity_score=severity_from_coverage(
            len(blind), len(tool_run.results),
        ),
        confidence_score=confidence_score(
            frequency=len(blind),
            reproducibility=1.0,
            cross_source_consistency=0.5,
            self_reference=True,
        ),
        is_actionable=False,
        candidate_knobs=(),
        rationale=(
            f"{len(blind)} SHOULD_TOOL_SUPPORT case(s) not "
            "dispatched — detector pattern gap."
        ),
        self_reference=True,
        inventory=inventory,
    )


# ---------------------------------------------------------------------------
# Sandbox v2.0
# ---------------------------------------------------------------------------


def discover_dead_mutation_knob(
    sandbox_report: dict[str, Any] | None,
    *,
    inventory: KnobInventory = DEFAULT_INVENTORY,
) -> DeficitRecord | None:
    """A knob is dead iff every step in the v2.0 sandbox accepted
    AND every per-step gate observable was constant. Detection is
    purely data-driven: no name is hardcoded — the knob's identity
    is read from ``steps[*].parameter``.
    """
    if sandbox_report is None:
        return None
    steps = sandbox_report.get("steps", [])
    if not steps:
        return None
    total = sandbox_report.get("total_steps", len(steps))
    accepted = sandbox_report.get("accepted_steps", 0)
    if accepted < total:
        return None        # some step failed — knob clearly matters
    metric_variance = _gate_metric_variance(steps)
    if metric_variance > 0:
        return None        # knob produced movement
    knob_names = {s.get("parameter") for s in steps if s.get("parameter")}
    # The sandbox enforces single-knob; we expect exactly one.
    if len(knob_names) != 1:
        return None
    knob = next(iter(knob_names))
    # Only flag the knob as dead when we recognise it (otherwise we'd
    # be claiming knowledge we don't have).
    if not inventory.is_known(knob):
        return None
    return DeficitRecord.build(
        category=DeficitCategory.DEAD_MUTATION_KNOB,
        source_module="desi.sandbox",
        source_case_ids=tuple(
            f"step_{s['step_id']}" for s in steps
        ),
        frequency=total,
        # severity = entire mutation budget wasted on this knob.
        severity_score=1.0,
        confidence_score=confidence_score(
            frequency=total,
            reproducibility=1.0,
            # cross-source: sandbox AND the gate's six observables.
            cross_source_consistency=1.0,
            self_reference=False,
        ),
        is_actionable=True,
        candidate_knobs=(knob,),
        rationale=(
            f"All {total} sandbox steps accepted with zero variance "
            f"across the six gate observables. Knob {knob!r} is "
            "decoupled from the v1.2+ evaluation surface."
        ),
        self_reference=False,
        inventory=inventory,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gate_metric_variance(steps: list[dict[str, Any]]) -> int:
    """Total movement across the six gate observables over a run."""
    observables = [
        "precision", "recall", "false_positives",
        "authority_blocks", "tool_precision", "hash_mismatches",
    ]
    moved = 0
    for key in observables:
        seen = {s.get(key) for s in steps}
        if len(seen) > 1:
            moved += 1
    return moved


__all__ = [
    "CaseResolution",
    "discover_authority_coverage",
    "discover_counterexample_coverage",
    "discover_dead_mutation_knob",
    "discover_false_block_reason",
    "discover_parser_coverage",
    "discover_recursion_configuration",
    "discover_tool_coverage",
    "discover_tool_dependency",
]

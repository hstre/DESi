"""v3.48 — GAP resolution strategies report.

Pflichtmetriken (directive § v3.48):

* ``resolved_count``       — best strategy's count
* ``unresolved_count``     — best strategy's count
* ``overcontrol``          — best strategy's count on
  the full corpus
* ``nc_resolution_fp``     — best strategy's
  overcontrol rate on NCs (trajectories with original
  final == SUPPORTED)
* ``replay_stability``     — deterministic replay
* ``best_strategy``        — strategy with the
  highest resolved_count; ties broken by lower
  overcontrol then SelectorKind declaration order

Stop rule: if every strategy has resolved_count == 0,
GAP_DETECTED is a robust terminal failure class.
Document and continue.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..gap_detected.state import (
    GAP_DETECTED_STATE, PAPER10_TERMINAL_GAP_COUNT,
)
from .resolution import (
    ResolutionOutcome, resolve_all_strategies_on_gaps,
    resolve_on_corpus,
)
from .strategies import StrategyKind


_SUPPORTED = 4.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    resolved_count: int
    unresolved_count: int
    overcontrol_count: int
    nc_count: int
    nc_resolution_fp: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "resolved_count": self.resolved_count,
            "unresolved_count":
                self.unresolved_count,
            "overcontrol_count":
                self.overcontrol_count,
            "nc_count": self.nc_count,
            "nc_resolution_fp":
                self.nc_resolution_fp,
        }


@dataclass(frozen=True)
class V348Report:
    gap_population: int
    strategy_results: tuple[StrategyResult, ...]
    best_strategy: str
    resolved_count: int
    unresolved_count: int
    overcontrol: int
    nc_resolution_fp: float
    terminal_failure_class: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_population": self.gap_population,
            "strategy_results": [
                r.to_dict() for r in self.strategy_results
            ],
            "best_strategy": self.best_strategy,
            "resolved_count": self.resolved_count,
            "unresolved_count":
                self.unresolved_count,
            "overcontrol": self.overcontrol,
            "nc_resolution_fp":
                self.nc_resolution_fp,
            "terminal_failure_class":
                self.terminal_failure_class,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _result_for(
    strategy: str,
    gap_outcomes: tuple[ResolutionOutcome, ...],
    corpus_outcomes: tuple[ResolutionOutcome, ...],
) -> StrategyResult:
    g_for = [
        o for o in gap_outcomes
        if o.strategy == strategy
    ]
    res = sum(1 for o in g_for if o.resolved)
    unres = sum(1 for o in g_for if not o.resolved)
    over_full = sum(
        1 for o in corpus_outcomes
        if o.strategy == strategy and o.overcontrol
    )
    nc_pool = [
        o for o in corpus_outcomes
        if o.strategy == strategy
        and o.original_final_support == _SUPPORTED
    ]
    nc_fp = (
        _round(over_full / len(nc_pool))
        if nc_pool else 0.0
    )
    return StrategyResult(
        strategy=strategy, resolved_count=res,
        unresolved_count=unres,
        overcontrol_count=over_full,
        nc_count=len(nc_pool),
        nc_resolution_fp=nc_fp,
    )


def _pick_best(
    results: tuple[StrategyResult, ...],
) -> StrategyResult:
    order = {
        k.value: i for i, k in enumerate(StrategyKind)
    }
    return min(
        results,
        key=lambda r: (
            -r.resolved_count, r.overcontrol_count,
            order[r.strategy],
        ),
    )


def _replay_stability() -> float:
    a = [
        o.to_dict()
        for o in resolve_all_strategies_on_gaps()
    ]
    b = [
        o.to_dict()
        for o in resolve_all_strategies_on_gaps()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V348Report:
    gap_outcomes = resolve_all_strategies_on_gaps()
    corpus_outcomes: list[ResolutionOutcome] = []
    for k in StrategyKind:
        corpus_outcomes.extend(
            resolve_on_corpus(k.value),
        )
    corpus_tuple = tuple(corpus_outcomes)
    results = tuple(
        _result_for(
            k.value, gap_outcomes, corpus_tuple,
        )
        for k in StrategyKind
    )
    best = _pick_best(results)
    replay = _replay_stability()

    all_zero = all(
        r.resolved_count == 0 for r in results
    )
    terminal = all_zero

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif terminal:
        verdict = "GAP_TERMINAL_FAILURE_CLASS"
    elif best.resolved_count >= PAPER10_TERMINAL_GAP_COUNT:
        verdict = "GAP_FULLY_RESOLVED"
    else:
        verdict = "GAP_PARTIALLY_RESOLVED"

    rationale = (
        f"INFO: gap_population "
        f"{PAPER10_TERMINAL_GAP_COUNT}",
        f"INFO: best_strategy {best.strategy} "
        f"(resolved {best.resolved_count}, "
        f"overcontrol {best.overcontrol_count}, "
        f"nc_fp {best.nc_resolution_fp})",
        f"INFO: terminal_failure_class {terminal} "
        f"(all strategies resolve 0)",
        f"INFO: per-strategy resolved counts "
        f"{[(r.strategy, r.resolved_count) for r in results]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V348Report(
        gap_population=PAPER10_TERMINAL_GAP_COUNT,
        strategy_results=results,
        best_strategy=best.strategy,
        resolved_count=best.resolved_count,
        unresolved_count=best.unresolved_count,
        overcontrol=best.overcontrol_count,
        nc_resolution_fp=best.nc_resolution_fp,
        terminal_failure_class=terminal,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_gap_resolution_artifact(
) -> dict[str, object]:
    gap_outcomes = resolve_all_strategies_on_gaps()
    return {
        "schema_version": "v3_48_gap_resolution",
        "outcomes": [
            o.to_dict() for o in gap_outcomes
        ],
        "outcome_count": len(gap_outcomes),
    }


def build_terminal_gap_claims_artifact(
) -> dict[str, object]:
    """One claim per terminal GAP case recording which
    strategies (if any) resolved it. Matches the
    directive's deliverable #4."""
    gap_outcomes = resolve_all_strategies_on_gaps()
    by_traj: dict[str, list[str]] = {}
    for o in gap_outcomes:
        if o.resolved:
            by_traj.setdefault(
                o.trajectory_id, [],
            ).append(o.strategy)
    from ..gap_detected.extractor import (
        terminal_gap_cases,
    )
    claims = []
    for i, c in enumerate(terminal_gap_cases()):
        resolved_by = by_traj.get(c.trajectory_id, [])
        claims.append({
            "claim_id": f"TG{i+1:03d}",
            "trajectory_id": c.trajectory_id,
            "source_corpus": c.source_corpus,
            "pattern": c.pattern,
            "trajectory_length":
                c.trajectory_length,
            "resolved_by_strategies":
                sorted(resolved_by),
            "text": (
                f"Terminal GAP trajectory "
                f"{c.trajectory_id} (pattern "
                f"{c.pattern}, length "
                f"{c.trajectory_length}) is resolved "
                f"by strategies: "
                f"{sorted(resolved_by) or 'none'}."
            ),
        })
    return {
        "schema_version":
            "v3_48_terminal_gap_claims",
        "claims": claims,
        "claim_count": len(claims),
    }


__all__ = [
    "StrategyResult", "V348Report",
    "build_gap_resolution_artifact",
    "build_report",
    "build_terminal_gap_claims_artifact",
]

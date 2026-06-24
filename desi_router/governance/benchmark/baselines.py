"""Baseline policies for the router benchmark.

A router only earns its name against opponents. Each baseline maps a DesiReport (+ availability
flags) to a RouterDecision, exactly like ``select_mode``. The point of the comparison is NOT to make
the DESi router win — it is to show whether it is *selectively* better: as safe as ``always_guarded``
on the dangerous cases while staying light on the clean ones. A router that always says "guarded" is
not safe, it is useless.
"""
from __future__ import annotations

from collections.abc import Callable

from desi_router.governance import modes as M
from desi_router.governance.modes import RouterDecision, select_mode
from desi_router.governance.report import DesiReport


def _d(report, mode, *, validate=False, may_update=False, preprompt="none"):
    return RouterDecision(task_id=report.task_id, chosen_mode=mode, reason="baseline",
                          preprompt_policy=preprompt, validator_required=validate,
                          persistent_state_update_allowed=may_update)


def no_router(report: DesiReport, **_) -> RouterDecision:
    # no governance at all: always answer, always allow the update, never verify
    return _d(report, M.NORMAL, may_update=True)


def always_normal(report: DesiReport, **_) -> RouterDecision:
    return _d(report, M.NORMAL, may_update=True)


def always_retrieval(report: DesiReport, **_) -> RouterDecision:
    return _d(report, M.RETRIEVAL, validate=True)


def always_state_slice(report: DesiReport, **_) -> RouterDecision:
    return _d(report, M.STATE_SLICE, may_update=True)


def always_guarded(report: DesiReport, **_) -> RouterDecision:
    return _d(report, M.GUARDED, validate=True, may_update=False, preprompt="guarded")


def simple_threshold(report: DesiReport, *, retrieval_available: bool = True, **_) -> RouterDecision:
    """A naive single-threshold router: ask if user-state missing, retrieve if no state, guard if
    any risk >= 0.5, else hand over the slice. No recovery, no anti-delphi, blind to the 0.4–0.5 band."""
    if report.user_specific_missing:
        return _d(report, M.ASK_USER)
    if not report.has_usable_state and retrieval_available:
        return _d(report, M.RETRIEVAL, validate=True)
    if max(report.risk_scores.values(), default=0.0) >= 0.5:
        return _d(report, M.GUARDED, validate=True, preprompt="guarded")
    return _d(report, M.STATE_SLICE, may_update=True)


def desi_router(report: DesiReport, *, retrieval_available: bool = True,
                anti_delphi_available: bool = False) -> RouterDecision:
    return select_mode(report, retrieval_available=retrieval_available,
                       anti_delphi_available=anti_delphi_available)


BASELINES: dict[str, Callable[..., RouterDecision]] = {
    "B0_no_router": no_router,
    "B1_always_normal": always_normal,
    "B2_always_retrieval": always_retrieval,
    "B3_always_state_slice": always_state_slice,
    "B4_always_guarded": always_guarded,
    "B5_simple_threshold": simple_threshold,
    "B6_desi_router": desi_router,
}

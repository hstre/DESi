"""Plausible-Wrong-Slice metrics — the honest pair, plus the per-subset breakdown.

The single most important number is ``false_clean_rate``: how often a plausible-wrong slice is routed
as **clean** (a light mode AND an allowed update). But optimising it alone is trivial — flag
everything — so it is always reported next to ``over_caution_rate`` on the TRUE-CLEAN controls. A
check earns its keep only if it drives false_clean down while keeping over_caution at zero.
"""
from __future__ import annotations

from desi_router.governance.benchmark.pws_cases import PWS_CASES, PWSCase

_LIGHT = {"normal_mode", "state_slice_mode"}


def _routed_clean(decision) -> bool:
    """The router treated the slice as settled: a light mode AND it may propose an update."""
    return decision.chosen_mode in _LIGHT and decision.persistent_state_update_allowed


def evaluate_pws(policy, *, aware: bool = True, cases: list[PWSCase] | None = None) -> dict:
    cases = cases or PWS_CASES
    traps = [c for c in cases if c.klass == "PWS"]
    cleans = [c for c in cases if c.klass == "CLEAN"]

    def run(c):
        rep = c.report(aware=aware)
        return policy(rep, retrieval_available=True, anti_delphi_available=False)

    trap_clean = sum(_routed_clean(run(c)) for c in traps)
    clean_escalated = sum(not _routed_clean(run(c)) for c in cleans)

    # per-subset: what THIS signal (missing_opposition) is responsible for vs. what it cannot close
    mo = [c for c in traps if c.detects_with == "missing_opposition"]
    other = [c for c in traps if c.detects_with != "missing_opposition"]
    mo_false_clean = sum(_routed_clean(run(c)) for c in mo)
    other_false_clean = sum(_routed_clean(run(c)) for c in other)

    def rate(num, den):
        return round(num / den, 3) if den else None

    return {
        "n_traps": len(traps), "n_clean": len(cleans),
        "false_clean_rate": rate(trap_clean, len(traps)),
        "pws_detection_rate": rate(len(traps) - trap_clean, len(traps)),
        "over_caution_rate": rate(clean_escalated, len(cleans)),
        "false_clean_opposition_subset": rate(mo_false_clean, len(mo)),
        "false_clean_other_subset": rate(other_false_clean, len(other)),
        "_subset_sizes": {"missing_opposition": len(mo), "needs_other_checks": len(other)},
    }

"""Plausible-Wrong-Slice metrics — the honest pair, plus the per-subset breakdown.

The single most important number is ``false_clean_rate``: how often a plausible-wrong slice SURVIVES
the attack (no vector fires → treated as settled). It is always reported next to ``over_caution_rate``
on the TRUE-CLEAN controls — optimising one alone is trivial. The metric routes every case through
``attack_slice`` (the unified #7 falsification pass), so it measures exactly the vehicle that gets
adopted, including the k-stability vector (which needs the case's widened report).
"""
from __future__ import annotations

from desi_router.governance.benchmark.pws_cases import PWS_CASES, PWSCase
from desi_router.governance.slice_attack import attack_slice

_SUBSETS = ("missing_opposition", "provenance_entropy", "scope_match",
            "supersession", "k_stability")


def _survived_as_clean(case: PWSCase, *, aware: bool) -> bool:
    """The slice survived the attack AND the decision would allow a settled update — i.e. it was
    treated as clean. A trap surviving is a false-clean; a control surviving is correct."""
    res = attack_slice(case.report(aware=aware), wide_report=case.wide_report(aware=aware))
    return res.survived and res.decision.persistent_state_update_allowed


def evaluate_pws(policy=None, *, aware: bool = True, cases: list[PWSCase] | None = None) -> dict:
    # ``policy`` is accepted for signature compatibility but unused: the attack vehicle is select_mode
    # internally. The blind/aware contrast comes from feeding (aware) or withholding (blind) the scan.
    cases = cases or PWS_CASES
    traps = [c for c in cases if c.klass == "PWS"]
    cleans = [c for c in cases if c.klass == "CLEAN"]

    def rate(num, den):
        return round(num / den, 3) if den else None

    trap_clean = sum(_survived_as_clean(c, aware=aware) for c in traps)
    clean_escalated = sum(not _survived_as_clean(c, aware=aware) for c in cleans)

    by_subset, sizes = {}, {}
    for s in _SUBSETS:
        grp = [c for c in traps if c.detects_with == s]
        sizes[s] = len(grp)
        by_subset[s] = rate(sum(_survived_as_clean(c, aware=aware) for c in grp), len(grp))

    return {
        "n_traps": len(traps), "n_clean": len(cleans),
        "false_clean_rate": rate(trap_clean, len(traps)),
        "pws_detection_rate": rate(len(traps) - trap_clean, len(traps)),
        "over_caution_rate": rate(clean_escalated, len(cleans)),
        "false_clean_by_subset": by_subset,
        "_subset_sizes": sizes,
    }

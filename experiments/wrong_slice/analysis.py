"""Paired analysis + pre-registered decision rule for the wrong-slice ablation.

Consumes RunResult records (``result_schema.py``) produced by the live harness
and computes, per the frozen design (PREREGISTRATION.md §6):

  * degeneration incidence per arm  (1 - admissible_rate)
  * PAIRED contrasts on (case_id, repetition, seed): correct vs each wrong arm,
    and each arm vs raw, via an exact two-sided McNemar test
  * a directional effect (absolute difference in degeneration incidence)
  * the pre-registered decision (H1 / H0-shrink / H2) against margin delta

Stdlib only. **No fabrication:** this operates solely on the records passed in.
With no records it returns an explicit "insufficient_data" verdict and never
invents numbers. It makes no result claims — it reports what the data say.
"""
from __future__ import annotations

from math import comb

from result_schema import RunResult


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value over discordant pairs (b, c)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def _pair_key(r: RunResult) -> tuple:
    return (r.case_id, r.repetition, r.seed)


def degeneration_incidence(results: list[RunResult], arm: str) -> dict:
    arm_rows = [r for r in results if r.arm == arm]
    n = len(arm_rows)
    degen = sum(1 for r in arm_rows if not r.admissible)
    return {
        "arm": arm,
        "n": n,
        "degenerate": degen,
        "incidence": (degen / n) if n else None,
    }


def paired_contrast(results: list[RunResult], arm_a: str, arm_b: str) -> dict:
    """Paired degeneration contrast arm_a vs arm_b over shared (case,rep,seed)."""
    a = {_pair_key(r): r for r in results if r.arm == arm_a}
    b = {_pair_key(r): r for r in results if r.arm == arm_b}
    shared = sorted(set(a) & set(b))
    # discordances on degeneration (degenerate == not admissible)
    b_fixed = sum(1 for k in shared if (not a[k].admissible) and b[k].admissible)
    c_broke = sum(1 for k in shared if a[k].admissible and (not b[k].admissible))
    inc_a = sum(1 for k in shared if not a[k].admissible)
    inc_b = sum(1 for k in shared if not b[k].admissible)
    n = len(shared)
    return {
        "arm_a": arm_a,
        "arm_b": arm_b,
        "n_pairs": n,
        "incidence_a": (inc_a / n) if n else None,
        "incidence_b": (inc_b / n) if n else None,
        # positive => arm_b degenerates more than arm_a (a is "better")
        "abs_diff_b_minus_a": ((inc_b - inc_a) / n) if n else None,
        "discordant_a_better": c_broke,
        "discordant_b_better": b_fixed,
        "mcnemar_p": mcnemar_exact_p(b_fixed, c_broke),
    }


def decide(contrast: dict, *, delta: float, alpha: float = 0.05) -> dict:
    """Apply the frozen decision rule for a correct-vs-wrong contrast.

    ``contrast`` must be paired_contrast(results, "correct", wrong_arm).
    Returns the pre-registered verdict and the corrected public phrasing.
    """
    n = contrast["n_pairs"]
    if n == 0:
        return {"verdict": "insufficient_data", "note": "no shared pairs"}
    # incidence_a = correct, incidence_b = wrong ; positive diff => wrong worse
    diff = contrast["abs_diff_b_minus_a"]   # wrong - correct
    p = contrast["mcnemar_p"]
    significant = p < alpha
    if diff >= delta and significant:
        verdict = "H1_selection_real"
        note = "correct beats matched wrong by >= delta; selection is real."
    elif abs(diff) < delta and not significant:
        verdict = "H0_shrink_to_context_selection"
        note = ("correct ~= matched wrong: narrow the claim to 'structured "
                "context hygiene/selection', NOT 'epistemic state selection'. "
                "Underpowered nulls are PRELIMINARY (see PREREGISTRATION.md §7).")
    elif diff < 0 and significant:
        verdict = "H2_wrong_structure_harmful"
        note = "matched wrong is WORSE than correct beyond delta (report explicitly)."
    else:
        verdict = "inconclusive"
        note = "effect/significance do not meet any pre-registered threshold."
    return {
        "verdict": verdict,
        "abs_diff_wrong_minus_correct": diff,
        "delta": delta,
        "mcnemar_p": p,
        "alpha": alpha,
        "significant": significant,
        "n_pairs": n,
        "note": note,
    }


def run_paired_analysis(results: list[RunResult], *, delta: float, alpha: float = 0.05) -> dict:
    """Full pre-registered analysis. Returns a JSON-serializable dict.

    Refuses to invent anything: with no records, verdict == 'insufficient_data'.
    """
    if not results:
        return {"verdict": "insufficient_data", "note": "no records provided"}
    arms = sorted({r.arm for r in results})
    incidences = {a: degeneration_incidence(results, a) for a in arms}
    wrong_arms = [a for a in ("wrong_permuted", "wrong_plausible") if a in arms]
    contrasts = {}
    decisions = {}
    if "correct" in arms:
        for w in wrong_arms:
            ct = paired_contrast(results, "correct", w)
            contrasts[f"correct_vs_{w}"] = ct
            decisions[w] = decide(ct, delta=delta, alpha=alpha)
        if "raw" in arms:
            contrasts["correct_vs_raw"] = paired_contrast(results, "correct", "raw")
    for w in wrong_arms:
        if "raw" in arms:
            contrasts[f"{w}_vs_raw"] = paired_contrast(results, w, "raw")
    return {
        "n_records": len(results),
        "arms": arms,
        "delta": delta,
        "alpha": alpha,
        "incidence": incidences,
        "contrasts": contrasts,
        "decisions": decisions,
    }

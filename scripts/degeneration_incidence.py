#!/usr/bin/env python3
"""Degeneration incidence on DriftBench: with vs without the DESi state layer.

Motivation (from external review, HF forum, 2026-06):

    "turn [the loop-trap observation] into a number: report
     loop-trap / degeneration incidence with vs without the layer ...
     You already found 'clean' low-density states that were actually loop
     traps - that's exactly the metric where the layer might genuinely win
     even when single-metric optima say it doesn't."

This script answers the *computable* part of that on the committed dataset
``data/driftbench/driftbench_compression.jsonl`` (N=1,525 paired trajectories):
does carrying the DESi epistemic state, instead of the raw transcript, reduce
the *incidence* of degenerate (high-drift / lock-in) trajectory states?

PRE-REGISTRATION (criteria fixed BEFORE looking at the per-threshold result, so
this is not a metric reverse-engineered to favour DESi):

  * A trajectory is "degenerate" under threshold tau if its drift score >= tau.
    The SAME tau is applied to both arms:
        - no-layer arm   -> raw_drift   (drift of the raw transcript)
        - with-layer arm -> desi_drift  (drift of the DESi state summary)
  * PRIMARY_TAU = 0.50  (drifted more than half-way off the intended
    trajectory := a majority-drifted state).
  * SENSITIVITY sweep over (0.30, 0.40, 0.50, 0.60, 0.70) is reported so the
    headline cannot rest on one hand-picked cut.
  * "Hard lock-in" is the dataset's own categorical label
    drift == "trajectory_lock_in" (the loop-trap analog), reported separately.
  * Comparison is PAIRED (same run_id, same scenario, two arms) and tested with
    an exact two-sided McNemar (binomial) test. N=1,525 -> well powered. This
    is the opposite regime from the n=5 ablations discussed alongside it: a
    null here would be informative; a null at n=5 would only be underpowered.

SCOPE / WHAT THIS DOES *NOT* CLAIM (kept explicit to avoid overstating):

  * This measures degeneration of the STATE REPRESENTATION, not of model
    BEHAVIOUR on a task. ``desi_drift`` is the drift of the compressed DESi
    state summary; ``raw_drift`` is the drift of the raw transcript. So the
    result is PARTLY ENTANGLED with the compression headline already reported
    (a short, structured state object trivially drifts less than a long
    transcript). Read the reduction as "the carried state stays on-trajectory",
    NOT as "DESi stops the model from looping". The latter is a behavioural
    claim this dataset cannot support.
  * The reviewer's full ``admissible_run`` (no_loop AND task_completed AND
    no_severe_role_adoption AND no_control_failure) needs the adversarial
    role-adoption sweep, which is a SEPARATE dataset and is NOT in this repo.
    This script does not pretend to cover loop / task-starvation /
    role-adoption / control-failure incidence.
  * The four structural ``*_preserved`` flags are constant (1 for all 1,525
    rows): they carry no variance and are therefore NOT used as a degeneration
    signal here. They are reported only as a transparency check.

No network, no LLM, no PRNG: pure recomputation over the committed file.

Usage:
    python scripts/degeneration_incidence.py
    python scripts/degeneration_incidence.py --json
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "driftbench" / "driftbench_compression.jsonl"

# --- pre-registered criteria (do not tune to the result) ---------------------
PRIMARY_TAU = 0.50
SENSITIVITY_TAUS = (0.30, 0.40, 0.50, 0.60, 0.70)
HARD_LOCK_IN_LABEL = "trajectory_lock_in"
RAW_KEY = "raw_drift"   # no-layer arm
DESI_KEY = "desi_drift"  # with-layer arm
# constant flags, reported for transparency only (not a degeneration signal)
PRESERVATION_FLAGS = (
    "constraint_preservation_preserved",
    "recovery_events_preserved",
    "lock_in_preserved",
    "branch_state_preserved",
)


def load(path: Path = DATA) -> list[dict]:
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value via the binomial on the discordant pairs.

    b = #(raw degenerate, desi not)  -- pairs the layer "fixed"
    c = #(desi degenerate, raw not)  -- pairs the layer "broke"
    Under H0 each discordant pair is 50/50; test b ~ Binomial(b+c, 0.5).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def incidence_at(rows: list[dict], tau: float) -> dict:
    n = len(rows)
    raw_deg = [r[RAW_KEY] >= tau for r in rows]
    desi_deg = [r[DESI_KEY] >= tau for r in rows]
    raw_n = sum(raw_deg)
    desi_n = sum(desi_deg)
    # paired discordances
    b = sum(1 for rd, dd in zip(raw_deg, desi_deg) if rd and not dd)  # layer fixed
    c = sum(1 for rd, dd in zip(raw_deg, desi_deg) if dd and not rd)  # layer broke
    return {
        "tau": tau,
        "n": n,
        "raw_incidence": raw_n / n,
        "desi_incidence": desi_n / n,
        "raw_count": raw_n,
        "desi_count": desi_n,
        "abs_reduction": (raw_n - desi_n) / n,
        "rel_reduction": (raw_n - desi_n) / raw_n if raw_n else 0.0,
        "pairs_layer_fixed": b,
        "pairs_layer_broke": c,
        "mcnemar_p": mcnemar_exact_p(b, c),
    }


def compute(rows: list[dict]) -> dict:
    n = len(rows)
    # hard lock-in subset (categorical loop-trap analog)
    lock = [r for r in rows if r["drift"] == HARD_LOCK_IN_LABEL]
    lock_primary = incidence_at(lock, PRIMARY_TAU) if lock else None

    # per-condition breakdown at the primary threshold
    by_condition: dict[str, dict] = {}
    for cond in sorted({r["condition"] for r in rows}):
        sub = [r for r in rows if r["condition"] == cond]
        by_condition[cond] = incidence_at(sub, PRIMARY_TAU)

    # per-model breakdown at the primary threshold
    by_model: dict[str, dict] = {}
    for m in sorted({r["model_id"] for r in rows}):
        sub = [r for r in rows if r["model_id"] == m]
        by_model[m] = incidence_at(sub, PRIMARY_TAU)

    return {
        "n": n,
        "primary": incidence_at(rows, PRIMARY_TAU),
        "sensitivity": [incidence_at(rows, t) for t in SENSITIVITY_TAUS],
        "hard_lock_in": lock_primary,
        "hard_lock_in_n": len(lock),
        "by_condition": by_condition,
        "by_model": by_model,
        "preservation_flags_constant": {
            f: (sum(r[f] for r in rows) == n) for f in PRESERVATION_FLAGS
        },
    }


def _fmt(s: dict) -> str:
    return (
        f"raw={s['raw_incidence']*100:5.1f}%  "
        f"desi={s['desi_incidence']*100:5.1f}%  "
        f"abs-red={s['abs_reduction']*100:5.1f}pp  "
        f"rel-red={s['rel_reduction']*100:5.1f}%  "
        f"(fixed={s['pairs_layer_fixed']} broke={s['pairs_layer_broke']} "
        f"p={s['mcnemar_p']:.2e})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    rows = load()
    s = compute(rows)
    if args.json:
        print(json.dumps(s, indent=2))
        return

    print(f"DriftBench degeneration incidence  (N={s['n']} paired trajectories)")
    print(f"  arm definition: no-layer={RAW_KEY}  with-layer={DESI_KEY}")
    print()
    print(f"PRIMARY  tau={PRIMARY_TAU}")
    print(f"  {_fmt(s['primary'])}")
    print()
    print("SENSITIVITY sweep (degenerate := drift >= tau)")
    for row in s["sensitivity"]:
        print(f"  tau={row['tau']:.2f}  {_fmt(row)}")
    print()
    if s["hard_lock_in"]:
        print(f"HARD LOCK-IN subset  (drift=={HARD_LOCK_IN_LABEL!r}, n={s['hard_lock_in_n']})")
        print(f"  {_fmt(s['hard_lock_in'])}")
        print()
    print(f"BY CONDITION  (tau={PRIMARY_TAU})")
    for cond, row in s["by_condition"].items():
        print(f"  {cond:<22} {_fmt(row)}")
    print()
    print(f"BY MODEL  (tau={PRIMARY_TAU})")
    for m, row in s["by_model"].items():
        print(f"  {m:<38} {_fmt(row)}")
    print()
    allc = all(s["preservation_flags_constant"].values())
    print(f"transparency: all four *_preserved flags constant(=1)? {allc} "
          f"(reported, NOT used as a degeneration signal)")
    print()
    print("CAVEAT: this is STATE-REPRESENTATION degeneration (desi_drift vs")
    print("raw_drift), partly entangled with the compression result. It is NOT")
    print("the behavioural loop-trap / task-starvation metric, which needs the")
    print("separate adversarial role-adoption sweep (not in this repo).")


if __name__ == "__main__":
    main()

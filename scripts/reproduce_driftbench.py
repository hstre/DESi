#!/usr/bin/env python3
"""Reproduce the DriftBench trajectory-state compression headline numbers.

Recomputes, directly from the committed dataset
(``data/driftbench/driftbench_compression.jsonl``), every figure reported in
README Section 7.1 "Context Compression Demo (N=1,525 DriftBench trajectories)":

    * mean raw transcript tokens / mean DESi state-summary tokens
    * mean compression ratio (~96.5%)
    * fraction of trajectories above 90% compression
    * drift-signal correlations: Pearson(raw_drift, severity) and
      Pearson(desi_drift, severity), and their ratio rho
    * the four structural preservation flags (1525/1525 each)

No network, no LLM calls, no PRNG: pure recomputation over the committed file.

Usage:
    python scripts/reproduce_driftbench.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "driftbench" / "driftbench_compression.jsonl"

PRESERVATION_FLAGS = (
    "constraint_preservation_preserved",
    "recovery_events_preserved",
    "lock_in_preserved",
    "branch_state_preserved",
)


def load(path: Path = DATA) -> list[dict]:
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def mean(rows: list[dict], key: str) -> float:
    return sum(r[key] for r in rows) / len(rows)


def pearson(rows: list[dict], x_key: str, y_key: str) -> float:
    n = len(rows)
    if n == 0:
        return 0.0
    xs = [r[x_key] for r in rows]
    ys = [r[y_key] for r in rows]
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:  # degenerate (constant) column, not a crash
        return 0.0
    return cov / (sx * sy)


def steiger_z(r1: float, r2: float, r12: float, n: int) -> tuple[float, float]:
    """Steiger's (1980) Z for two *dependent* correlations sharing one variable.

    Here: r1 = r(raw_drift, severity) and r2 = r(desi_drift, severity) are
    measured on the SAME n trajectories and share the severity variable, so
    their difference cannot be tested as if independent; the correlation
    between the two drift columns (r12) enters the variance. Closed-form and
    deterministic (no PRNG): Fisher z-transforms with the Dunn & Clark
    covariance term, two-sided p via the normal CDF (math.erf).

    Returns (Z, p_two_sided). This is what the headline ratio rho needs to be
    more than a point estimate: p quantifies whether rho is distinguishable
    from 1.0 on this sample.
    """
    z1, z2 = math.atanh(r1), math.atanh(r2)
    rbar = (r1 + r2) / 2.0
    rbar2 = rbar * rbar
    # Dunn & Clark (1969) covariance of the two z-transformed correlations,
    # as used in Steiger's Z*2 with the mean-r simplification (Steiger 1980).
    psi = r12 * (1.0 - 2.0 * rbar2) - 0.5 * rbar2 * (1.0 - 2.0 * rbar2 - r12 * r12)
    s = psi / ((1.0 - rbar2) ** 2)
    z = (z1 - z2) * math.sqrt((n - 3) / (2.0 - 2.0 * s))
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    return z, p


def compute(rows: list[dict]) -> dict:
    n = len(rows)
    r_raw = pearson(rows, "raw_drift", "drift_severity")
    r_desi = pearson(rows, "desi_drift", "drift_severity")
    r_raw_desi = pearson(rows, "raw_drift", "desi_drift")
    z, p = steiger_z(r_desi, r_raw, r_raw_desi, n)
    return {
        "n": n,
        "mean_raw_tokens": mean(rows, "raw_tokens"),
        "mean_desi_tokens": mean(rows, "desi_state_tokens"),
        "mean_compression_ratio": mean(rows, "compression_ratio"),
        "frac_over_90pct": sum(1 for r in rows if r["compression_ratio"] > 0.90) / n,
        "corr_raw": r_raw,
        "corr_desi": r_desi,
        "corr_raw_vs_desi": r_raw_desi,
        "rho": r_desi / r_raw if r_raw else float("nan"),
        "steiger_z": z,
        "steiger_p_two_sided": p,
        "preservation": {f: sum(r[f] for r in rows) for f in PRESERVATION_FLAGS},
    }


def main() -> None:
    rows = load()
    s = compute(rows)
    print(f"N trajectories            = {s['n']}")
    print(f"mean raw_tokens           = {s['mean_raw_tokens']:.1f}")
    print(f"mean desi_state_tokens    = {s['mean_desi_tokens']:.1f}")
    print(f"mean compression_ratio    = {s['mean_compression_ratio']:.4f}  ({s['mean_compression_ratio']*100:.1f}%)")
    print(f"trajectories >90% compr.  = {int(s['frac_over_90pct']*s['n'])}/{s['n']}")
    print(f"Pearson(raw_drift , sev)  = {s['corr_raw']:.4f}")
    print(f"Pearson(desi_drift, sev)  = {s['corr_desi']:.4f}")
    print(f"preservation ratio rho    = {s['rho']:.4f}")
    print(f"Steiger Z (dep. corr.)    = {s['steiger_z']:.4f}  "
          f"(p two-sided = {s['steiger_p_two_sided']:.4f})")
    verdict = ("rho > 1 is statistically distinguishable from 1.0"
               if s["steiger_p_two_sided"] < 0.05
               else "rho is NOT statistically distinguishable from 1.0 — "
                    "treat 'signal preserved (and slightly sharpened)' as the claim, "
                    "not 'signal improved'")
    print(f"  -> {verdict}")
    for f, c in s["preservation"].items():
        print(f"  {f:<34} {c}/{s['n']}")


if __name__ == "__main__":
    main()

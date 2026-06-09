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
    xs = [r[x_key] for r in rows]
    ys = [r[y_key] for r in rows]
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy)


def compute(rows: list[dict]) -> dict:
    n = len(rows)
    r_raw = pearson(rows, "raw_drift", "drift_severity")
    r_desi = pearson(rows, "desi_drift", "drift_severity")
    return {
        "n": n,
        "mean_raw_tokens": mean(rows, "raw_tokens"),
        "mean_desi_tokens": mean(rows, "desi_state_tokens"),
        "mean_compression_ratio": mean(rows, "compression_ratio"),
        "frac_over_90pct": sum(1 for r in rows if r["compression_ratio"] > 0.90) / n,
        "corr_raw": r_raw,
        "corr_desi": r_desi,
        "rho": r_desi / r_raw,
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
    for f, c in s["preservation"].items():
        print(f"  {f:<34} {c}/{s['n']}")


if __name__ == "__main__":
    main()

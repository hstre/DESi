"""Cycle-5 time-to-attention analyser.

Documentation-only. No DESi-side change. Computes:

    latency_i = first_focus_loop_i - creation_loop_i

for every reconstructed candidate (cycle 1 EN OR cycle 2 critique-nav)
across three sources:

  1. hand-authored adversarial suite (data/adversarial/*.json)
  2. hand-authored generalization suite (data/generalization/*.json)
  3. translated native DES trajectory (cycle_1 conservative output)

Reports per-source mean, median, variance, and per-candidate latencies.

Sets LATENCY_DISTRIBUTION_MISMATCH per user rule:
    real_DES_mean > 2 * synthetic_mean

`first_focus_loop` is computed by reconstructing the same logic as
`experiments/.../cycle_4/downstream_effect.py` (smallest later loop
where `step.focus_claim_id == created_claim`). Doing so without
relying on cycle-4's analyser keeps this cycle self-contained.

Usage:
    PYTHONPATH=src python3 \\
      experiments/external_reality_challenge/en_reconstruction/cycle_5/time_to_attention.py
"""
from __future__ import annotations

import json
import pathlib
import statistics
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from desi.diagnostics import compute_all  # noqa: E402
from desi.trajectory_loader import load_trajectory  # noqa: E402


MISMATCH_THRESHOLD = 2.0  # user rule: flag iff real > 2x synthetic


@dataclass(frozen=True)
class Latency:
    fixture: str
    claim_id: str
    creation_loop: int
    first_focus_loop: int | None
    latency: int | None     # None when no later focus exists
    via: str                # hypothesis_builder | falsifier


def collect_latencies(traj_path: pathlib.Path) -> list[Latency]:
    """Walk a trajectory's reconstructed candidates and compute
    per-candidate latency."""
    traj = load_trajectory(str(traj_path))
    metrics = compute_all(traj)
    cands = list(metrics.en_reconstruction.candidates) + \
            list(metrics.critique_navigation.candidates)
    out: list[Latency] = []
    sorted_steps = sorted(traj.steps, key=lambda s: s.loop_index)
    for c in cands:
        first_focus: int | None = None
        for s in sorted_steps:
            if s.loop_index <= c.loop_index:
                continue
            if s.focus_claim_id == c.target_claim:
                first_focus = s.loop_index
                break
        latency = (first_focus - c.loop_index) if first_focus is not None else None
        # Tag which sub-role produced this candidate.
        from desi.diagnostics import ENCandidate
        via = "hypothesis_builder" if isinstance(c, ENCandidate) else "falsifier"
        out.append(Latency(
            fixture=traj_path.name,
            claim_id=c.target_claim or "",
            creation_loop=c.loop_index,
            first_focus_loop=first_focus,
            latency=latency,
            via=via,
        ))
    return out


def stats(latencies: list[int]) -> dict:
    """Mean / median / variance for a list of integer latencies."""
    if not latencies:
        return {"n": 0, "mean": None, "median": None, "variance": None}
    return {
        "n": len(latencies),
        "mean": round(statistics.fmean(latencies), 2),
        "median": statistics.median(latencies),
        "variance": (
            round(statistics.variance(latencies), 2)
            if len(latencies) > 1 else 0.0
        ),
    }


def render_markdown(rows_per_source: dict[str, list[Latency]]) -> str:
    lines: list[str] = []
    lines.append("# Cycle 5 — time-to-attention distributions")
    lines.append("")
    lines.append("**Metric**: `latency = first_focus_loop - creation_loop` for "
                 "each reconstructed candidate.")
    lines.append("")

    # Per-source statistics
    lines.append("## Per-source statistics")
    lines.append("")
    lines.append("| Source | candidates | with-latency | mean | median | variance |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    src_stats: dict[str, dict] = {}
    for src, rows in rows_per_source.items():
        lats = [r.latency for r in rows if r.latency is not None]
        s = stats(lats)
        src_stats[src] = s
        lines.append(
            f"| `{src}` "
            f"| {len(rows)} "
            f"| {len(lats)} "
            f"| {s['mean'] if s['mean'] is not None else '—'} "
            f"| {s['median'] if s['median'] is not None else '—'} "
            f"| {s['variance'] if s['variance'] is not None else '—'} |"
        )
    lines.append("")

    # LATENCY_DISTRIBUTION_MISMATCH evaluation
    lines.append("## LATENCY_DISTRIBUTION_MISMATCH flag")
    lines.append("")
    lines.append(f"**Rule**: TRUE iff `real_DES_mean > {MISMATCH_THRESHOLD} * synthetic_mean`.")
    lines.append("")
    real_mean = src_stats.get("native_DES_real", {}).get("mean")
    syn_n10 = src_stats.get("hand_authored_n10_adversarial", {}).get("n", 0)
    syn_n20 = src_stats.get("hand_authored_n20_generalization", {}).get("n", 0)
    syn_n_total = syn_n10 + syn_n20
    if syn_n_total == 0:
        synthetic_mean = None
    else:
        # Combined synthetic mean across both hand-authored suites.
        all_syn = [
            r.latency for src in (
                "hand_authored_n10_adversarial",
                "hand_authored_n20_generalization",
            )
            for r in rows_per_source[src]
            if r.latency is not None
        ]
        synthetic_mean = (
            round(statistics.fmean(all_syn), 2) if all_syn else None
        )
    if real_mean is None and synthetic_mean is None:
        flag = "UNDEFINED (no candidates anywhere)"
    elif synthetic_mean is None or synthetic_mean == 0:
        flag = (
            "UNDEFINED (synthetic_mean has no candidates / is zero; "
            "the `> 2x` ratio is not well-formed)"
        )
    else:
        ratio = real_mean / synthetic_mean
        is_mismatch = ratio > MISMATCH_THRESHOLD
        flag = (
            f"{'TRUE' if is_mismatch else 'FALSE'} "
            f"(real_mean={real_mean}, synthetic_mean={synthetic_mean}, "
            f"ratio={round(ratio, 2)})"
        )
    lines.append(f"- real_DES_mean: `{real_mean}`")
    lines.append(f"- synthetic_mean (combined hand-authored): `{synthetic_mean}`")
    lines.append(f"- **LATENCY_DISTRIBUTION_MISMATCH**: **{flag}**")
    lines.append("")

    # Per-source candidate detail
    lines.append("## Per-candidate latency (all sources)")
    lines.append("")
    for src, rows in rows_per_source.items():
        lines.append(f"### `{src}`")
        lines.append("")
        if not rows:
            lines.append("- (no reconstructed candidates on this source)")
            lines.append("")
            continue
        lines.append("| Fixture | Claim | Created @ | First focus @ | Latency | Via |")
        lines.append("|---|---|---:|---:|---:|---|")
        for r in rows:
            lines.append(
                f"| `{r.fixture}` "
                f"| `{r.claim_id}` "
                f"| {r.creation_loop} "
                f"| {r.first_focus_loop if r.first_focus_loop is not None else '—'} "
                f"| {r.latency if r.latency is not None else '—'} "
                f"| `{r.via}` |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    sources = {
        "hand_authored_n10_adversarial":
            sorted(pathlib.Path("data/adversarial").glob("*.json")),
        "hand_authored_n20_generalization":
            sorted(pathlib.Path("data/generalization").glob("*.json")),
        "native_DES_real": [
            pathlib.Path(
                "experiments/external_reality_challenge/cycle_1/"
                "des_translated_conservative.json"
            )
        ],
    }
    rows_per_source: dict[str, list[Latency]] = {}
    for label, paths in sources.items():
        rows: list[Latency] = []
        for p in paths:
            rows.extend(collect_latencies(p))
        rows_per_source[label] = rows
    print(render_markdown(rows_per_source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

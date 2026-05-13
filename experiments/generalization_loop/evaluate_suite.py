"""Run DESi deterministic stack on the n=20 generalization suite.

Produces a metrics dict + a markdown report. Reused as-is for the
baseline AND for each cycle re-evaluation (cycle_N/eval_gen.md).

Usage:
    python -m experiments.generalization_loop.evaluate_suite \\
        --suite data/generalization \\
        --out-json outputs/generalization_loop/baseline_metrics.json \\
        --out-md  experiments/generalization_loop/baseline_report.md \\
        --label   baseline

Comparisons against `_meta.expected_*` are best-effort, not authoritative
verdicts -- only the user can judge "false positive" in the end. We just
record per-fixture deltas honestly.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from desi.diagnostics import compute_all  # noqa: E402
from desi.phase_detector import detect_phases  # noqa: E402
from desi.trajectory_loader import load_trajectory  # noqa: E402


def _phase_overlaps(phases) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    spans = list(phases.phases)
    for i, a in enumerate(spans):
        for b in spans[i + 1:]:
            if a.start_loop <= b.end_loop and b.start_loop <= a.end_loop:
                overlaps.append((a.name, b.name))
    return overlaps


def _phase_malformed(phases) -> list[str]:
    return [p.name for p in phases.phases if p.start_loop > p.end_loop]


def _expected_hits_satisfied(detector_hits, expected):
    return {key: detector_hits.get(key, False) for key in expected}


def evaluate_one(path: pathlib.Path) -> dict:
    raw = json.loads(path.read_text())
    meta = raw.get("_meta", {}) or {}
    traj = load_trajectory(str(path))
    metrics = compute_all(traj)
    phases = detect_phases(traj)
    composite_labels = [c.label for c in metrics.en_classifications_composite]
    detector_hits = {
        "branch_explosion": metrics.branch_explosion.detected,
        "mild_stagnation": metrics.mild_stagnation.detected,
        "step_coherence_violation": metrics.step_coherence.detected,
        "penultimate_en_candidate": metrics.penultimate.has_candidate,
        "attractor_lock": bool(metrics.attractor.candidate_claim_ids),
        "borderline_chain": metrics.borderline_chain.detected,
        "any_genuine_transformation_confirmed":
            "genuine_transformation_confirmed" in composite_labels,
        "any_recovered_after_high_eni":
            "recovered_after_high_eni" in composite_labels,
        "any_stuck_high_eni":
            "stuck_high_eni" in composite_labels,
    }
    expected_hits = list(meta.get("expected_detector_hits", []) or [])
    hit_outcome = _expected_hits_satisfied(detector_hits, expected_hits)
    missed = [k for k, v in hit_outcome.items() if not v]
    spurious = [k for k, v in detector_hits.items() if v and k not in expected_hits]
    return {
        "fixture": path.name,
        "trajectory_id": traj.trajectory_id,
        "n_steps": metrics.n_steps,
        "n_en_events": metrics.n_en_events,
        "phases": [{"name": p.name, "start": p.start_loop, "end": p.end_loop, "confidence": p.confidence} for p in phases.phases],
        "phase_overlaps": _phase_overlaps(phases),
        "phase_malformed": _phase_malformed(phases),
        "detector_hits": detector_hits,
        "composite_en_labels": composite_labels,
        "novelty_recoveries": [asdict(nr) for nr in metrics.novelty_recoveries],
        "failure_mode_summary": {"terminal": metrics.failure.terminal, "per_step": list(metrics.failure.per_step)},
        "expected": {
            "failure_mode": meta.get("expected_failure_mode"),
            "detector_hits": expected_hits,
            "risk": meta.get("expected_risk"),
            "why_unseen": meta.get("why_this_is_unseen"),
        },
        "deltas": {
            "expected_hits_resolved": hit_outcome,
            "missed_expected_hits": missed,
            "spurious_hits": spurious,
        },
    }


def aggregate(records):
    total = len(records)
    n_with_phase_overlaps = sum(1 for r in records if r["phase_overlaps"])
    n_with_malformed = sum(1 for r in records if r["phase_malformed"])
    total_missed = sum(len(r["deltas"]["missed_expected_hits"]) for r in records)
    total_spurious = sum(len(r["deltas"]["spurious_hits"]) for r in records)
    detector_fire_counts = {}
    for r in records:
        for k, v in r["detector_hits"].items():
            if v:
                detector_fire_counts[k] = detector_fire_counts.get(k, 0) + 1
    return {
        "n_fixtures": total,
        "n_with_phase_overlaps": n_with_phase_overlaps,
        "n_with_malformed_phases": n_with_malformed,
        "total_missed_expected_hits": total_missed,
        "total_spurious_hits": total_spurious,
        "detector_fire_counts": detector_fire_counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="data/generalization")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--label", default="suite")
    args = ap.parse_args()
    suite_dir = pathlib.Path(args.suite)
    files = sorted(suite_dir.glob("*.json"))
    if not files:
        print(f"No fixtures found in {suite_dir}", file=sys.stderr)
        return 2
    records = [evaluate_one(p) for p in files]
    agg = aggregate(records)
    out_json = pathlib.Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"label": args.label, "aggregate": agg, "records": records}, indent=2, sort_keys=True))
    out_md = pathlib.Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Generalization suite evaluation — {args.label}", "", f"n_fixtures: **{agg['n_fixtures']}**", f"phase overlaps: **{agg['n_with_phase_overlaps']}**", f"malformed phase spans: **{agg['n_with_malformed_phases']}**", "", "## Detector fire counts", "", "| Detector | Fires |", "|---|---:|"]
    for k in sorted(agg["detector_fire_counts"]):
        lines.append(f"| `{k}` | {agg['detector_fire_counts'][k]} |")
    out_md.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_json} and {out_md}")
    print(json.dumps(agg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

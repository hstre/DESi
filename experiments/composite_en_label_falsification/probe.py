"""confirmed_genuine_en falsification probe.

ORIGINAL FRAMING (NOW REPUDIATED): This file was authored under the
mistaken belief that birth(B) reduces to "the composite classifier
produces genuine_transformation_confirmed for some EN event". Paper 0
defines birth(B) = (D, R, F, P, ΔQ), a 5-tuple. The 5 -> 1 reduction
was a category error caught by the user; see
`../semantic_drift_report.md` for the post-mortem.

CORRECTED FRAMING: This probe measures `confirmed_genuine_en(trajectory)`,
defined as:

    confirmed_genuine_en(traj) = 1 iff
        compute_all(traj).en_classifications_composite contains at
        least one entry with label == "genuine_transformation_confirmed".

It does NOT measure birth(B). It measures one composite EN label.
That signal is operationally relevant to DESi (Phase III's first
trigger gate uses it), but is not equivalent to Paper 0's tuple.

This probe does NOT modify DESi. It runs the unchanged compute_all on
the given fixture and reports.

Usage:
    PYTHONPATH=src python3 experiments/composite_en_label_falsification/probe.py FIXTURE.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from desi.diagnostics import compute_all  # noqa: E402
from desi.phase_detector import PHASE_III, detect_phases  # noqa: E402
from desi.trajectory_loader import load_trajectory  # noqa: E402


def confirmed_genuine_en(trajectory) -> dict:
    metrics = compute_all(trajectory)
    phases = detect_phases(trajectory)
    composite_labels = [c.label for c in metrics.en_classifications_composite]
    confirmed_count = sum(1 for l in composite_labels if l == "genuine_transformation_confirmed")
    phase_iii = next((p for p in phases.phases if p.name == PHASE_III), None)
    return {
        "trajectory_id": trajectory.trajectory_id,
        "n_en_events": metrics.n_en_events,
        "composite_labels": composite_labels,
        "novelty_recoveries": [
            {"loop": nr.loop_index, "dup_delta": nr.dup_delta,
             "novel_next": nr.novel_claims_next, "recovered": nr.recovered}
            for nr in metrics.novelty_recoveries
        ],
        "phase_iii_present": phase_iii is not None,
        "phase_iii_span": None if phase_iii is None else (phase_iii.start_loop, phase_iii.end_loop),
        "confirmed_count": confirmed_count,
        "confirmed_genuine_en": 1 if confirmed_count >= 1 else 0,
    }


def run(path: pathlib.Path) -> dict:
    traj = load_trajectory(str(path))
    return confirmed_genuine_en(traj)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe.py <fixture.json> [more.json ...]", file=sys.stderr)
        return 2
    rows = []
    for arg in sys.argv[1:]:
        rows.append(run(pathlib.Path(arg)))
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

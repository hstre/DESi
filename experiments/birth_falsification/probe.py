"""Birth(B) falsification probe.

Operational definition of birth(B):
  birth(B) = 1 iff `compute_all(trajectory).en_classifications_composite`
  contains at least one entry with label == "genuine_transformation_confirmed".

Falsification task: produce trajectories DESi *should* recognise as having a
genuine breakthrough (per paper7 / DES semantics) but for which the existing
detector returns birth(B) = 0. Each fixture is a hypothesis under test.

This probe does NOT modify DESi. It runs the unchanged compute_all on the
given fixture and reports birth(B) plus auxiliary signals (Phase III, the
composite label that was actually produced, novelty_recovery flags).

Usage:
    PYTHONPATH=src python3 experiments/birth_falsification/probe.py FIXTURE.json
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


def birth(trajectory) -> dict:
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
        "birth_B": 1 if confirmed_count >= 1 else 0,
    }


def run(path: pathlib.Path) -> dict:
    traj = load_trajectory(str(path))
    return birth(traj)


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

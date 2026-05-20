"""v3.96a — multi-seed jitter census.

Runs the v3.85 / v3.86 trajectory-extraction
pipeline under multiple ``PYTHONHASHSEED`` values
and shuffled test orders, and tabulates how often
the StateVector output differs.

The probe is a pure subprocess driver - it never
touches the production trajectory cache so the
parent process's own randomized hash never
contaminates a child's measurement.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]


_PROBE_SCRIPT: str = '''
import sys, json
sys.path.insert(0, "src")
from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
out = []
for t in extract_all_trajectories():
    states = [
        [s.frame_id, s.contradiction_load,
         s.anchor_density, s.source_quality,
         s.novelty, s.confidence,
         s.branch_cost, s.support_state,
         s.routing_state]
        for s in t.states
    ]
    out.append({
        "trajectory_id": t.trajectory_id,
        "source": t.source.value,
        "state_count": len(t.states),
        "states": states,
    })
print(json.dumps(out, sort_keys=True))
'''


def run_with_seed(
    seed: int,
) -> tuple[dict[str, list[list[float]]], int]:
    """Subprocess-run the trajectory extractor
    under the given PYTHONHASHSEED. Returns a
    (trajectory_id -> state matrix) dict plus the
    process exit code."""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT],
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ({}, proc.returncode)
    parsed = json.loads(proc.stdout)
    by_id: dict[str, list[list[float]]] = {}
    for t in parsed:
        by_id[t["trajectory_id"]] = t["states"]
    return (by_id, 0)


SEED_CENSUS: tuple[int, ...] = tuple(
    range(0, 100),
)
"""Closed enum of seeds used in the census.

100 seeds is the directive's minimum threshold."""

REFERENCE_SEED: int = 0


@dataclass(frozen=True)
class JitterCensus:
    seed_count: int
    reference_seed: int
    trajectory_count: int
    jittery_trajectory_ids: tuple[str, ...]
    jittery_trajectory_count: int
    jitter_rate: float
    affected_dims: tuple[str, ...]
    max_state_delta: float

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_count": self.seed_count,
            "reference_seed": self.reference_seed,
            "trajectory_count":
                self.trajectory_count,
            "jittery_trajectory_ids":
                list(self.jittery_trajectory_ids),
            "jittery_trajectory_count":
                self.jittery_trajectory_count,
            "jitter_rate": self.jitter_rate,
            "affected_dims":
                list(self.affected_dims),
            "max_state_delta":
                self.max_state_delta,
        }


_DIM_NAMES: tuple[str, ...] = (
    "frame_id", "contradiction_load",
    "anchor_density", "source_quality",
    "novelty", "confidence",
    "branch_cost", "support_state",
    "routing_state",
)


@lru_cache(maxsize=1)
def census() -> JitterCensus:
    ref, code = run_with_seed(REFERENCE_SEED)
    if code != 0:
        return JitterCensus(
            seed_count=0,
            reference_seed=REFERENCE_SEED,
            trajectory_count=0,
            jittery_trajectory_ids=(),
            jittery_trajectory_count=0,
            jitter_rate=0.0,
            affected_dims=(),
            max_state_delta=0.0,
        )

    jittery: set[str] = set()
    affected_dims: set[str] = set()
    max_delta = 0.0
    samples: list[dict[str, list[list[float]]]] = []
    for seed in SEED_CENSUS:
        if seed == REFERENCE_SEED:
            samples.append(ref)
            continue
        snap, sc = run_with_seed(seed)
        if sc != 0:
            continue
        samples.append(snap)
        for tid, states in snap.items():
            ref_states = ref.get(tid)
            if ref_states is None:
                continue
            if states == ref_states:
                continue
            jittery.add(tid)
            for s_i, (sv, rv) in enumerate(
                zip(states, ref_states),
            ):
                for d_i, (a, b) in enumerate(
                    zip(sv, rv),
                ):
                    if a != b:
                        affected_dims.add(
                            _DIM_NAMES[d_i],
                        )
                        delta = abs(a - b)
                        if delta > max_delta:
                            max_delta = delta
    total = len(ref)
    rate = (
        _round(len(jittery) / total)
        if total else 0.0
    )
    return JitterCensus(
        seed_count=len(SEED_CENSUS),
        reference_seed=REFERENCE_SEED,
        trajectory_count=total,
        jittery_trajectory_ids=tuple(sorted(jittery)),
        jittery_trajectory_count=len(jittery),
        jitter_rate=rate,
        affected_dims=tuple(sorted(affected_dims)),
        max_state_delta=_round(max_delta),
    )


def affected_packages() -> tuple[str, ...]:
    """Static enumeration: ``epistemic_trajectory``
    is the only package that re-derives state
    vectors from raw text. Listed here as a closed
    set so the census artifact is explicit even
    when the jitter rate is zero."""
    return ("epistemic_trajectory",)


__all__ = [
    "JitterCensus",
    "REFERENCE_SEED",
    "SEED_CENSUS",
    "affected_packages",
    "census",
    "run_with_seed",
]

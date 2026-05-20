"""v3.120c — historical stress replay.

Subprocess-replay the v3.120 pre-T10 rule under
multiple PYTHONHASHSEED values. Each subprocess
recomputes the allowed/blocked partition and the
TPR/FAR for the rule against the v3.119
ground-truth labels.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache


_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]


SEEDS: tuple[int, ...] = tuple(range(0, 10))


_PROBE_SCRIPT: str = """
import sys, json
sys.path.insert(0, "src")
from desi.pre_t10_rule.decision import (
    allowed_pool_count, blocked_pool_count,
    false_activation_rate, true_case_recall,
    historical_gate_flip_count,
)
print(json.dumps({
    "allowed": allowed_pool_count(),
    "blocked": blocked_pool_count(),
    "far": false_activation_rate(),
    "tpr": true_case_recall(),
    "hgfc": historical_gate_flip_count(),
}, sort_keys=True))
"""


def _seed_subprocess(seed: int) -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT],
        cwd=str(_REPO_ROOT),
        env=env, capture_output=True,
        text=True, check=False,
    )
    if proc.returncode != 0:
        return {}
    return json.loads(proc.stdout)


@dataclass(frozen=True)
class StressCell:
    seed: int
    allowed: int
    blocked: int
    far: float
    tpr: float
    hgfc: int

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "far": self.far,
            "tpr": self.tpr,
            "hgfc": self.hgfc,
        }


@lru_cache(maxsize=1)
def all_stress_cells() -> tuple[StressCell, ...]:
    out: list[StressCell] = []
    for s in SEEDS:
        snap = _seed_subprocess(s)
        out.append(StressCell(
            seed=s,
            allowed=int(
                snap.get("allowed", 0),
            ),
            blocked=int(
                snap.get("blocked", 0),
            ),
            far=float(snap.get("far", 0.0)),
            tpr=float(snap.get("tpr", 0.0)),
            hgfc=int(snap.get("hgfc", 0)),
        ))
    return tuple(out)


__all__ = [
    "SEEDS",
    "StressCell",
    "all_stress_cells",
]

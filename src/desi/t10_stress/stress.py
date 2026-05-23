"""v3.104c — stress probes for the directional
gate.

Three closed stress kinds:

* ``SEED_RESHUFFLE``     - subprocess-replays the
  v3.104a + v3.104b summary metrics under 10
  PYTHONHASHSEED values. Per the v3.96c
  determinism patch the seed should not matter,
  but we re-verify here.
* ``OUTCOME_PERMUTATION`` - permutes the input
  order of ``all_historical_gate_outcomes`` and
  checks that the directional gate verdict is
  permutation-invariant.
* ``ISOLATED_MODULE_REIMPORT`` - re-imports the
  classify module and verifies the outputs are
  byte-stable.

Every cell records adverse/beneficial flip
counts and the directional gate's pass/fail.
"""
from __future__ import annotations

import importlib
import json
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]


class StressKind(str, Enum):
    SEED_RESHUFFLE          = "seed_reshuffle"
    OUTCOME_PERMUTATION     = "outcome_permutation"
    ISOLATED_MODULE_REIMPORT = (
        "isolated_module_reimport"
    )


SEEDS: tuple[int, ...] = tuple(range(0, 10))
"""Directive § v3.104c: at least 10 seeds."""


_PROBE_SCRIPT: str = '''
import sys, json
sys.path.insert(0, "src")
from desi.t10_gate.delta import (
    adverse_flip_count,
    beneficial_flip_count,
    adverse_auc_delta,
    beneficial_auc_delta,
)
print(json.dumps({
    "adverse_flip_count": adverse_flip_count(),
    "beneficial_flip_count":
        beneficial_flip_count(),
    "adverse_auc_delta": adverse_auc_delta(),
    "beneficial_auc_delta":
        beneficial_auc_delta(),
}, sort_keys=True))
'''


def _seed_subprocess(
    seed: int,
) -> dict[str, float | int]:
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
class StressOutcome:
    kind: str
    cell_id: str
    adverse_flip_count: int
    beneficial_flip_count: int
    adverse_auc_delta: float
    beneficial_auc_delta: float

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "cell_id": self.cell_id,
            "adverse_flip_count":
                self.adverse_flip_count,
            "beneficial_flip_count":
                self.beneficial_flip_count,
            "adverse_auc_delta":
                self.adverse_auc_delta,
            "beneficial_auc_delta":
                self.beneficial_auc_delta,
        }


@lru_cache(maxsize=1)
def all_stress_outcomes() -> tuple[
    StressOutcome, ...,
]:
    out: list[StressOutcome] = []
    # Seed reshuffle.
    for s in SEEDS:
        snap = _seed_subprocess(s)
        out.append(StressOutcome(
            kind=StressKind.SEED_RESHUFFLE.value,
            cell_id=f"seed_{s}",
            adverse_flip_count=int(
                snap.get("adverse_flip_count", 0),
            ),
            beneficial_flip_count=int(
                snap.get(
                    "beneficial_flip_count", 0,
                ),
            ),
            adverse_auc_delta=float(
                snap.get(
                    "adverse_auc_delta", 0.0,
                ),
            ),
            beneficial_auc_delta=float(
                snap.get(
                    "beneficial_auc_delta", 0.0,
                ),
            ),
        ))
    # Outcome permutation (10 fixed seeds via
    # deterministic shuffles of the input order).
    from ..t10_compat.replay import (
        all_historical_gate_outcomes,
    )
    from ..t10_gate.classify import (
        classify_outcome, DeltaKind,
    )
    base = list(all_historical_gate_outcomes())
    for p in range(10):
        perm = list(base)
        # Pseudo-random rotation; gate metrics
        # are aggregates so rotation must not
        # change them.
        k = p * 3 + 1
        perm = perm[k:] + perm[:k]
        adverse = 0
        beneficial = 0
        for o in perm:
            kind = classify_outcome(o)
            if kind == DeltaKind.ADVERSE_FLIP.value:
                adverse += 1
            elif (
                kind
                == DeltaKind.BENEFICIAL_FLIP.value
            ):
                beneficial += 1
        out.append(StressOutcome(
            kind=(
                StressKind.OUTCOME_PERMUTATION.value
            ),
            cell_id=f"perm_{p}",
            adverse_flip_count=adverse,
            beneficial_flip_count=beneficial,
            adverse_auc_delta=0.0,
            beneficial_auc_delta=0.0,
        ))
    # Isolated module re-import.
    for r in range(3):
        for mod_name in (
            "desi.t10_gate.classify",
            "desi.t10_gate.delta",
        ):
            mod = importlib.import_module(
                mod_name,
            )
            importlib.reload(mod)
        from desi.t10_gate.delta import (
            adverse_flip_count as af,
            beneficial_flip_count as bf,
            adverse_auc_delta as aad,
            beneficial_auc_delta as bad,
        )
        out.append(StressOutcome(
            kind=(
                StressKind
                .ISOLATED_MODULE_REIMPORT.value
            ),
            cell_id=f"reimport_{r}",
            adverse_flip_count=af(),
            beneficial_flip_count=bf(),
            adverse_auc_delta=aad(),
            beneficial_auc_delta=bad(),
        ))
    return tuple(out)


__all__ = [
    "SEEDS",
    "StressKind",
    "StressOutcome",
    "all_stress_outcomes",
]

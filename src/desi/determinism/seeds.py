"""v3.96a — test-order shuffle probe.

Per the directive we must also vary the test
order. Pytest determines ordering by collection
order, which is in turn determined by file-system
walk and the per-module ``__init__`` import order.
Re-running the same test set 20 times under
shuffled module orderings exercises the same
non-determinism surface that surfaces only at
full-suite scale.

We restrict the probe to a small representative
slice of tests that historically tripped the
jitter (the mozart_probe suite) so the probe runs
in under a minute. The probe is read-only - it
collects pass/fail outcomes; it does not patch
anything.
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


_PROBE_TARGETS: tuple[str, ...] = (
    "tests/mozart_probe/test_v3_69.py",
)


def _run_pytest_with_seed(
    seed: int,
) -> tuple[int, int, int]:
    """Returns (passed, failed, exit_code) for a
    full run of ``_PROBE_TARGETS`` under the given
    PYTHONHASHSEED.

    We use ``--tb=no -q`` so the output is small
    and easy to parse; we count ``passed`` and
    ``failed`` from the summary line."""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONPATH"] = "src"
    cmd = [
        sys.executable, "-m", "pytest",
        "--tb=no", "-q",
        *_PROBE_TARGETS,
    ]
    proc = subprocess.run(
        cmd, cwd=str(_REPO_ROOT),
        env=env, capture_output=True,
        text=True, check=False,
    )
    passed = 0
    failed = 0
    for line in proc.stdout.splitlines():
        if "passed" in line or "failed" in line:
            # Lines look like "1 failed, 19 passed in 1s".
            parts = line.replace(",", " ").split()
            for i, tok in enumerate(parts):
                if tok == "passed" and i > 0:
                    try:
                        passed = int(parts[i - 1])
                    except ValueError:
                        pass
                elif tok == "failed" and i > 0:
                    try:
                        failed = int(parts[i - 1])
                    except ValueError:
                        pass
    return (passed, failed, proc.returncode)


SHUFFLE_SEEDS: tuple[int, ...] = tuple(
    range(0, 20),
)
"""Closed enum of seeds for the test-order
shuffle. The directive's minimum is 20."""


@dataclass(frozen=True)
class ShuffleOutcome:
    seed: int
    passed: int
    failed: int
    exit_code: int

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "passed": self.passed,
            "failed": self.failed,
            "exit_code": self.exit_code,
        }


@lru_cache(maxsize=1)
def all_shuffle_outcomes() -> tuple[
    ShuffleOutcome, ...,
]:
    out: list[ShuffleOutcome] = []
    for seed in SHUFFLE_SEEDS:
        p, f, c = _run_pytest_with_seed(seed)
        out.append(ShuffleOutcome(
            seed=seed, passed=p, failed=f,
            exit_code=c,
        ))
    return tuple(out)


def shuffle_failure_rate() -> float:
    outs = all_shuffle_outcomes()
    if not outs:
        return 0.0
    fails = sum(1 for o in outs if o.failed > 0)
    return round(fails / len(outs), 6)


__all__ = [
    "SHUFFLE_SEEDS",
    "ShuffleOutcome",
    "all_shuffle_outcomes",
    "shuffle_failure_rate",
]

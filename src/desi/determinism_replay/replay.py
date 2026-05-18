"""v3.96d - subprocess-driven replay of every
registered historical sprint under multiple
PYTHONHASHSEED values.

For each (sprint, seed) pair we run a subprocess
that imports the sprint's report module, calls
``build_report().to_dict()``, dumps canonical
JSON, and prints a sha256 digest of the bytes.

If two seeds yield the same digest the sprint's
output is byte-stable; if they differ the sprint
inherits seed jitter from somewhere upstream
(post-patch, none should).
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

from .historical import (
    HISTORICAL_SPRINTS, SprintEntry,
)


_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]


REPLAY_SEEDS: tuple[int, ...] = tuple(
    range(0, 5),
)
"""Five PYTHONHASHSEED values.

Combined with HISTORICAL_SPRINTS this yields 25
sprints * 5 seeds = 125 subprocess runs - well
above the directive's 50-replay floor."""


def _replay_script(module_path: str) -> str:
    return f'''
import sys, json, hashlib
sys.path.insert(0, "src")
mod = __import__("{module_path}", fromlist=["build_report"])
report = mod.build_report().to_dict()
# Drop the volatile rationale field so we measure
# the stable content, not the human-readable log.
report.pop("rationale", None)
blob = json.dumps(
    report, sort_keys=True, separators=(",", ":"),
).encode("utf-8")
print(hashlib.sha256(blob).hexdigest())
'''


def _replay_one(
    sprint: SprintEntry, seed: int,
) -> str:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    proc = subprocess.run(
        [
            sys.executable, "-c",
            _replay_script(sprint.module_path),
        ],
        cwd=str(_REPO_ROOT),
        env=env, capture_output=True,
        text=True, check=False,
    )
    if proc.returncode != 0:
        return f"ERROR:{proc.returncode}"
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else "ERROR:NO_OUTPUT"


@dataclass(frozen=True)
class ReplayOutcome:
    sprint_id: str
    family: str
    digests: tuple[str, ...]
    stable: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "sprint_id": self.sprint_id,
            "family": self.family,
            "digests": list(self.digests),
            "stable": self.stable,
        }


@lru_cache(maxsize=1)
def all_replay_outcomes() -> tuple[
    ReplayOutcome, ...,
]:
    out: list[ReplayOutcome] = []
    for sprint in HISTORICAL_SPRINTS:
        digests: list[str] = []
        for seed in REPLAY_SEEDS:
            digests.append(_replay_one(sprint, seed))
        unique = set(digests)
        stable = (
            len(unique) == 1
            and not any(
                d.startswith("ERROR:")
                for d in unique
            )
        )
        out.append(ReplayOutcome(
            sprint_id=sprint.sprint_id,
            family=sprint.family,
            digests=tuple(digests),
            stable=stable,
        ))
    return tuple(out)


def total_replay_count() -> int:
    return (
        len(HISTORICAL_SPRINTS)
        * len(REPLAY_SEEDS)
    )


__all__ = [
    "REPLAY_SEEDS",
    "ReplayOutcome",
    "all_replay_outcomes",
    "total_replay_count",
]

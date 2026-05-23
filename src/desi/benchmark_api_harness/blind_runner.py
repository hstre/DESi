"""v33.3 - blind evaluation runner.

Runs the harness results under neutral anonymous labels. The scorer
sees only an anonymous label and objective result properties
(validated, replay-bound) - never the benchmark name or adapter
identity. Scoring is therefore label-invariant: no benchmark can be
favoured, and DESi cannot adapt its output to a known benchmark.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .harness import run_all
from .result_validator import validate

_BLIND_SALT = "v33_3_benchmark_harness_blind"


def _anon_key(task_id: str) -> str:
    return hashlib.sha256(
        (_BLIND_SALT + "::" + task_id).encode("utf-8"),
    ).hexdigest()


@dataclass(frozen=True)
class AnonRun:
    anon_label: str
    validated: bool
    replay_bound: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "anon_label": self.anon_label,
            "validated": self.validated,
            "replay_bound": self.replay_bound,
        }


def _ordered():
    return sorted(run_all(), key=lambda tr: _anon_key(tr[0].task_id))


def anon_runs() -> tuple[AnonRun, ...]:
    out: list[AnonRun] = []
    for i, (_, result) in enumerate(_ordered()):
        out.append(AnonRun(
            anon_label=f"run_{i}",
            validated=validate(result),
            replay_bound=result.is_replay_bound(),
        ))
    return tuple(out)


def sealed_map() -> dict[str, str]:
    """anon_label -> benchmark_name. Post-hoc only; never used by the
    scorer."""
    return {
        f"run_{i}": task.benchmark_name
        for i, (task, _) in enumerate(_ordered())
    }


def _objective_score(run: AnonRun) -> float:
    return 1.0 if (run.validated and run.replay_bound) else 0.0


def blind_scores() -> dict[str, float]:
    return {r.anon_label: _objective_score(r) for r in anon_runs()}


def _leaks_benchmark(run: AnonRun) -> bool:
    blob = "|".join(str(v) for v in run.to_dict().values())
    return any(
        name in blob for name in sealed_map().values()
    )


def blind_evaluation_integrity() -> float:
    """1.0 iff no anonymous run leaks its benchmark name and scoring
    is label-invariant (relabelling does not change any score)."""
    runs = anon_runs()
    if not runs:
        return 0.0
    if any(_leaks_benchmark(r) for r in runs):
        return 0.0
    # label-invariance: scores depend only on objective properties
    relabelled = tuple(
        AnonRun(f"x_{i}", r.validated, r.replay_bound)
        for i, r in enumerate(runs)
    )
    base = [_objective_score(r) for r in runs]
    swapped = [_objective_score(r) for r in relabelled]
    return 1.0 if base == swapped else 0.0


__all__ = [
    "AnonRun",
    "anon_runs",
    "blind_evaluation_integrity",
    "blind_scores",
    "sealed_map",
]

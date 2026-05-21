"""v35.3 - honest benchmark summary across the v35/v34 runs.

Aggregates one summary row per benchmark run, each carrying an
explicit provenance class so real (connector-loaded) runs are never
confused with synthetic/in-repo fixture runs. Scores are the mean of
each run's reported metrics - no inflation, no projection.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from desi.benchmark_runs_rendering import rendering_metrics
from desi.benchmark_runs_repro import reproducibility_metrics
from desi.external_benchmarks_drift import drift_run_metrics
from desi.external_benchmarks_search import search_run_metrics

PROV_OFFLINE_REFERENCE = "offline_reference_dataset"
PROV_SYNTHETIC_FIXTURE = "synthetic_inline_fixture"
PROV_IN_REPO_FIXTURE = "in_repo_fixture"

PROVENANCE_CLASSES: tuple[str, ...] = (
    PROV_OFFLINE_REFERENCE, PROV_SYNTHETIC_FIXTURE,
    PROV_IN_REPO_FIXTURE,
)


def _mean(d: dict[str, float]) -> float:
    return round(sum(d.values()) / len(d), 6) if d else 0.0


def _anchor(name: str, d: dict[str, float]) -> str:
    parts = [name] + [f"{k}={d[k]}" for k in sorted(d)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


@dataclass(frozen=True)
class RunSummary:
    name: str
    family: str
    provenance_class: str
    score: float
    metrics: tuple[tuple[str, float], ...]
    replay_anchor: str

    @property
    def is_real_external(self) -> bool:
        return self.provenance_class == PROV_OFFLINE_REFERENCE

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "family": self.family,
            "provenance_class": self.provenance_class,
            "score": self.score,
            "metrics": [list(m) for m in self.metrics],
            "replay_anchor": self.replay_anchor,
            "is_real_external": self.is_real_external,
        }


def _row(name: str, family: str, prov: str,
         metrics: dict[str, float]) -> RunSummary:
    return RunSummary(
        name=name,
        family=family,
        provenance_class=prov,
        score=_mean(metrics),
        metrics=tuple(sorted(metrics.items())),
        replay_anchor=_anchor(name, metrics),
    )


def run_summaries() -> tuple[RunSummary, ...]:
    return (
        _row("real_drift", "Drift", PROV_OFFLINE_REFERENCE,
             drift_run_metrics()),
        _row("real_search", "SearchCompression",
             PROV_OFFLINE_REFERENCE, search_run_metrics()),
        _row("reproducibility", "Reproducibility",
             PROV_SYNTHETIC_FIXTURE, reproducibility_metrics()),
        _row("scientific_rendering", "ScientificRendering",
             PROV_IN_REPO_FIXTURE, rendering_metrics()),
    )


def real_vs_synthetic_visibility() -> float:
    """1.0 iff every run carries a known provenance class (real vs
    synthetic vs in-repo is always explicit)."""
    rows = run_summaries()
    if not rows:
        return 0.0
    ok = sum(
        1 for r in rows
        if r.provenance_class in set(PROVENANCE_CLASSES)
    )
    return round(ok / len(rows), 6)


def real_run_names() -> tuple[str, ...]:
    return tuple(r.name for r in run_summaries() if r.is_real_external)


def synthetic_run_names() -> tuple[str, ...]:
    return tuple(
        r.name for r in run_summaries() if not r.is_real_external
    )


__all__ = [
    "PROVENANCE_CLASSES",
    "PROV_IN_REPO_FIXTURE",
    "PROV_OFFLINE_REFERENCE",
    "PROV_SYNTHETIC_FIXTURE",
    "RunSummary",
    "real_run_names",
    "real_vs_synthetic_visibility",
    "run_summaries",
    "synthetic_run_names",
]

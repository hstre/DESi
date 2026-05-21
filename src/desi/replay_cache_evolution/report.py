"""v29.0 - Baseline Measurement report.

Pflichtmetriken (directive § v29.0):

* runtime_visibility
* artifact_stability
* recompute_visibility
* cache_opportunity_visibility
* replay_stability

Killerfrage: "Kann DESi ihre eigenen Infrastrukturkosten
explizit sichtbar machen?"

Measures the current (uncached) rebuild cost of representative
deterministic workloads as a recompute count, exposes the cache
opportunities, and pins the artifact hashes. Nothing is changed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .artifact_hashes import all_anchors, anchors_signature
from .baseline import (
    baseline_recompute_count, output_hashes, workloads,
)
from .metrics import (
    artifact_stability, cache_opportunity_visibility,
    recompute_visibility, replay_stability, runtime_visibility,
)

VERDICT_VISIBLE = "INFRA_COST_VISIBLE"
VERDICT_OPAQUE = "INFRA_COST_OPAQUE"
VERDICT_HALT = "BASELINE_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_VISIBLE, VERDICT_OPAQUE, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{w.name}|{w.seed}|{w.work}|{w.repeat}"
        for w in workloads()
    ]
    parts.append(anchors_signature())
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, replay: float, runtime: float, artifact: float,
    recompute: float, opportunity: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        runtime < _FLOOR
        or artifact < 1.0
        or recompute < _FLOOR
        or opportunity < _FLOOR
    ):
        return VERDICT_OPAQUE
    return VERDICT_VISIBLE


@dataclass(frozen=True)
class V290Report:
    workload_count: int
    baseline_recompute_count: int
    cacheable_workload_count: int
    runtime_visibility: float
    artifact_stability: float
    recompute_visibility: float
    cache_opportunity_visibility: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "workload_count": self.workload_count,
            "baseline_recompute_count":
                self.baseline_recompute_count,
            "cacheable_workload_count":
                self.cacheable_workload_count,
            "runtime_visibility": self.runtime_visibility,
            "artifact_stability": self.artifact_stability,
            "recompute_visibility": self.recompute_visibility,
            "cache_opportunity_visibility":
                self.cache_opportunity_visibility,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V290Report:
    runtime = runtime_visibility()
    artifact = artifact_stability()
    recompute = recompute_visibility()
    opportunity = cache_opportunity_visibility()
    replay = replay_stability()
    halt = replay < 1.0
    cacheable = sum(1 for w in workloads() if w.is_cacheable())
    verdict = _recommendation(
        replay=replay, runtime=runtime, artifact=artifact,
        recompute=recompute, opportunity=opportunity,
    )
    rationale = (
        f"INFO: {len(workloads())} rebuild workloads; baseline "
        f"recompute count {baseline_recompute_count()} (sum of "
        f"repeats); {cacheable} cacheable",
        "INFO: cost is measured as deterministic recompute "
        "operations (the reproducible proxy for wall-clock); "
        "wall-clock is observed live but never stored",
        f"{'PASS' if runtime >= _FLOOR else 'FAIL'}: "
        f"runtime_visibility {runtime} >= 0.90",
        f"{'PASS' if artifact >= 1.0 else 'FAIL'}: "
        f"artifact_stability {artifact}",
        f"{'PASS' if recompute >= _FLOOR else 'FAIL'}: "
        f"recompute_visibility {recompute} >= 0.90",
        f"{'PASS' if opportunity >= _FLOOR else 'FAIL'}: "
        f"cache_opportunity_visibility {opportunity} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V290Report(
        workload_count=len(workloads()),
        baseline_recompute_count=baseline_recompute_count(),
        cacheable_workload_count=cacheable,
        runtime_visibility=runtime,
        artifact_stability=artifact,
        recompute_visibility=recompute,
        cache_opportunity_visibility=opportunity,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_baseline_artifact() -> dict[str, object]:
    return {
        "schema_version": "v29_0_replay_cache_baseline",
        "disclaimer": (
            "Baseline measurement of DESi's infrastructure cost. "
            "Cost is measured deterministically as the number of "
            "recompute operations (cache misses) for "
            "representative rebuild workloads - the reproducible "
            "proxy for wall-clock cost; observed wall-clock is "
            "confirmed live but never stored (non-deterministic). "
            "Artifact hashes are pinned so a later cache "
            "optimisation can be proven byte-identical. Nothing "
            "is changed here. Replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "workloads": [w.to_dict() for w in workloads()],
        "baseline_recompute_count": baseline_recompute_count(),
        "output_hashes": dict(sorted(output_hashes().items())),
        "artifact_anchors": dict(sorted(all_anchors().items())),
        "runtime_visibility": runtime_visibility(),
        "artifact_stability": artifact_stability(),
        "recompute_visibility": recompute_visibility(),
        "cache_opportunity_visibility":
            cache_opportunity_visibility(),
        "replay_stability": replay_stability(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "VERDICT_VISIBLE",
    "V290Report",
    "build_baseline_artifact",
    "build_report",
]

"""v35.1 - real drift run scorecards.

One traceable scorecard per drift task across all three families,
binding each result to the external dataset's provenance and content
hash, the mapped claim/core drift, the refusal flag and the replay
hash.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.benchmark_api import BenchmarkResult
from desi.external_benchmarks import NormalizedTask

from .agentdrift_runner import agentdrift_results
from .beliefshift_runner import beliefshift_results
from .memevo_runner import memevo_results

_CORE_DIMS = (
    "governance_drift", "lineage_drift", "artifact_drift",
    "authority_drift", "replay_drift",
)


@dataclass(frozen=True)
class DriftRunScorecard:
    family: str
    task_id: str
    kind: str
    claim_drift: float
    core_drift_total: float
    refused: bool
    provenance: str
    dataset_hash: str
    replay_hash: str
    governance_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "task_id": self.task_id,
            "kind": self.kind,
            "claim_drift": self.claim_drift,
            "core_drift_total": self.core_drift_total,
            "refused": self.refused,
            "provenance": self.provenance,
            "dataset_hash": self.dataset_hash,
            "replay_hash": self.replay_hash,
            "governance_status": self.governance_status,
        }


def all_drift_results() -> tuple[tuple[NormalizedTask, BenchmarkResult], ...]:
    return (
        beliefshift_results() + memevo_results() + agentdrift_results()
    )


def _card(nt: NormalizedTask, res: BenchmarkResult) -> DriftRunScorecard:
    m = res.metric_map()
    return DriftRunScorecard(
        family=nt.family,
        task_id=nt.task_id,
        kind=nt.kind,
        claim_drift=m.get("claim_drift", 0.0),
        core_drift_total=sum(m.get(d, 0.0) for d in _CORE_DIMS),
        refused=res.is_refusal(),
        provenance=nt.provenance,
        dataset_hash=nt.dataset_content_hash,
        replay_hash=res.replay_hash,
        governance_status=res.governance_status,
    )


def drift_scorecards() -> tuple[DriftRunScorecard, ...]:
    return tuple(_card(nt, res) for nt, res in all_drift_results())


__all__ = [
    "DriftRunScorecard",
    "all_drift_results",
    "drift_scorecards",
]

"""v35.0 - External Dataset Connector Layer report.

Pflichtmetriken (directive § v35.0):

* dataset_version_visibility
* dataset_hash_visibility
* task_normalization_integrity
* governance_independence
* replay_stability

Killerfrage: "Kann DESi echte externe Benchmarkdaten replay-stabil
ingestieren?"

Builds the network-free connector layer: external benchmark datasets
are loaded from local files, versioned, hashed, normalised and
replay-bound. Governance is read from the core, never from the
dataset. Honesty note: in this environment the datasets are
locally-vendored reference sets in the published families' formats,
not live downloads of the official suites.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.frozen_baseline import governance_signature
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .benchmark_registry import BENCHMARK_FAMILIES, dataset_families
from .dataset_loader import load_all, network_free
from .task_normalizer import (
    all_normalized_tasks, task_normalization_integrity,
)

VERDICT_INGESTED = "EXTERNAL_CONNECTORS_REPLAY_STABLE"
VERDICT_PARTIAL = "EXTERNAL_CONNECTORS_PARTIAL"
VERDICT_HALT = "EXTERNAL_CONNECTORS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_INGESTED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def dataset_version_visibility() -> float:
    datasets = load_all()
    if not datasets:
        return 0.0
    ok = sum(1 for d in datasets if d.version)
    return round(ok / len(datasets), 6)


def dataset_hash_visibility() -> float:
    datasets = load_all()
    if not datasets:
        return 0.0
    ok = sum(
        1 for d in datasets if d.byte_hash and d.content_hash
    )
    return round(ok / len(datasets), 6)


def governance_independence() -> float:
    """1.0 iff the governance signature is invariant across loading
    and normalising every external dataset."""
    base = governance_signature()
    load_all()
    all_normalized_tasks()
    return 1.0 if governance_signature() == base else 0.0


def replay_stability() -> float:
    """1.0 iff dataset hashes are reproducible, normalisation keys
    are reproducible, and the core replay layer is stable."""
    a = [d.content_hash for d in load_all()]
    b = [d.content_hash for d in load_all()]
    if a != b:
        return 0.0
    ka = [t.replay_key() for t in all_normalized_tasks()]
    kb = [t.replay_key() for t in all_normalized_tasks()]
    if ka != kb:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def connector_metrics() -> dict[str, float]:
    return {
        "dataset_version_visibility": dataset_version_visibility(),
        "dataset_hash_visibility": dataset_hash_visibility(),
        "task_normalization_integrity":
            task_normalization_integrity(),
        "governance_independence": governance_independence(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = connector_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = connector_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_INGESTED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V350Report:
    families: tuple[str, ...]
    dataset_count: int
    task_count: int
    network_free: bool
    dataset_version_visibility: float
    dataset_hash_visibility: float
    task_normalization_integrity: float
    governance_independence: float
    replay_stability: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "families": list(self.families),
            "dataset_count": self.dataset_count,
            "task_count": self.task_count,
            "network_free": self.network_free,
            "dataset_version_visibility":
                self.dataset_version_visibility,
            "dataset_hash_visibility": self.dataset_hash_visibility,
            "task_normalization_integrity":
                self.task_normalization_integrity,
            "governance_independence": self.governance_independence,
            "replay_stability": self.replay_stability,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V350Report:
    m = connector_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    datasets = load_all()
    tasks = all_normalized_tasks()
    rationale = (
        f"INFO: network-free connector ({network_free()}); loaded "
        f"{len(datasets)} local datasets for families "
        f"{list(dataset_families())}; normalised {len(tasks)} tasks",
        "INFO: datasets are locally-vendored reference sets in the "
        "published families' formats - NOT live downloads, NOT "
        "official leaderboard scores; provenance is labelled per "
        "dataset",
        f"{'PASS' if m['dataset_version_visibility'] >= _FLOOR else 'FAIL'}"
        f": dataset_version_visibility "
        f"{m['dataset_version_visibility']} >= 0.95",
        f"{'PASS' if m['dataset_hash_visibility'] >= _FLOOR else 'FAIL'}"
        f": dataset_hash_visibility {m['dataset_hash_visibility']} "
        f">= 0.95 (byte + content hash per dataset)",
        f"{'PASS' if m['task_normalization_integrity'] >= _FLOOR else 'FAIL'}"
        f": task_normalization_integrity "
        f"{m['task_normalization_integrity']} >= 0.95 (every task "
        f"bound to dataset version + hash)",
        f"{'PASS' if m['governance_independence'] >= _FLOOR else 'FAIL'}"
        f": governance_independence {m['governance_independence']} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V350Report(
        families=BENCHMARK_FAMILIES,
        dataset_count=len(datasets),
        task_count=len(tasks),
        network_free=network_free(),
        dataset_version_visibility=m["dataset_version_visibility"],
        dataset_hash_visibility=m["dataset_hash_visibility"],
        task_normalization_integrity=m["task_normalization_integrity"],
        governance_independence=m["governance_independence"],
        replay_stability=replay,
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_connectors_artifact() -> dict[str, object]:
    m = connector_metrics()
    return {
        "schema_version": "v35_0_external_connectors",
        "disclaimer": (
            "Network-free external benchmark connector layer. "
            "External datasets enter DESi only as local files, which "
            "are versioned, hashed (byte + content), normalised and "
            "replay-bound; governance is read from the core, never "
            "from the dataset. IMPORTANT honesty note: in this "
            "environment the datasets are locally-vendored reference "
            "sets in the published benchmark families' formats. They "
            "are NOT live downloads of the official published suites "
            "and their scores are NOT official leaderboard results. "
            "The connector is built so that dropping the published "
            "dataset files into the local datasets directory makes "
            "the same pipeline run against them unchanged. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "network_free": network_free(),
        "families": list(BENCHMARK_FAMILIES),
        "datasets": [d.to_dict() for d in load_all()],
        "dataset_version_visibility": m["dataset_version_visibility"],
        "dataset_hash_visibility": m["dataset_hash_visibility"],
        "task_normalization_integrity":
            m["task_normalization_integrity"],
        "governance_independence": m["governance_independence"],
        "replay_stability": m["replay_stability"],
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_INGESTED",
    "VERDICT_PARTIAL",
    "V350Report",
    "build_connectors_artifact",
    "build_report",
    "connector_metrics",
    "dataset_hash_visibility",
    "dataset_version_visibility",
    "governance_independence",
    "replay_stability",
]

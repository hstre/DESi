"""v34.2 - Output Drift & Reproducibility Benchmark Run report.

Pflichtmetriken (directive § v34.2):

* output_identity
* metric_identity
* citation_identity
* artifact_identity
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Outputs reproduzierbar
erzeugen?"

Runs the same workload five times and verifies that outputs,
metrics, citations, sections, artifacts and replay hashes are
byte-identical across runs. Same input -> same output.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .artifact_identity import (
    artifact_identity, citation_identity, metric_identity,
    output_identity, replay_hash_identity, section_identity,
)
from .determinism_scorecard import determinism_scorecards
from .output_tasks import REPEATS

VERDICT_REPRODUCIBLE = "REPRODUCIBILITY_RUN_PASSED"
VERDICT_PARTIAL = "REPRODUCIBILITY_RUN_PARTIAL"
VERDICT_HALT = "REPRODUCIBILITY_RUN_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_REPRODUCIBLE, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def replay_stability() -> float:
    """1.0 iff replay hashes are identical across repeats and the
    core replay layer is stable."""
    if replay_hash_identity() < 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def reproducibility_metrics() -> dict[str, float]:
    return {
        "output_identity": output_identity(),
        "metric_identity": metric_identity(),
        "citation_identity": citation_identity(),
        "artifact_identity": artifact_identity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = reproducibility_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = reproducibility_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_REPRODUCIBLE
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V342Report:
    repeats: int
    output_identity: float
    metric_identity: float
    citation_identity: float
    artifact_identity: float
    section_identity: float
    replay_stability: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "repeats": self.repeats,
            "output_identity": self.output_identity,
            "metric_identity": self.metric_identity,
            "citation_identity": self.citation_identity,
            "artifact_identity": self.artifact_identity,
            "section_identity": self.section_identity,
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


def build_report() -> V342Report:
    m = reproducibility_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: repeated the workload {REPEATS}x; every snapshot "
        f"recomputed from scratch (not cached object identity)",
        f"{'PASS' if m['output_identity'] >= _FLOOR else 'FAIL'}: "
        f"output_identity {m['output_identity']} >= 0.95",
        f"{'PASS' if m['metric_identity'] >= _FLOOR else 'FAIL'}: "
        f"metric_identity {m['metric_identity']} >= 0.95",
        f"{'PASS' if m['citation_identity'] >= _FLOOR else 'FAIL'}: "
        f"citation_identity {m['citation_identity']} >= 0.95",
        f"{'PASS' if m['artifact_identity'] >= _FLOOR else 'FAIL'}: "
        f"artifact_identity {m['artifact_identity']} >= 0.95 "
        f"(section_identity {section_identity()})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V342Report(
        repeats=REPEATS,
        output_identity=m["output_identity"],
        metric_identity=m["metric_identity"],
        citation_identity=m["citation_identity"],
        artifact_identity=m["artifact_identity"],
        section_identity=section_identity(),
        replay_stability=replay,
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_reproducibility_artifact() -> dict[str, object]:
    m = reproducibility_metrics()
    return {
        "schema_version": "v34_2_reproducibility_run",
        "disclaimer": (
            "Controlled reproducibility benchmark run. The same "
            "workload (the v33 harness suite plus the output-port "
            "citation and section surfaces) is executed five times "
            "and every observable - outputs, metrics, citations, "
            "sections, artifacts and replay hashes - is verified "
            "byte-identical across runs. Snapshots are recomputed "
            "from scratch on each repeat, so identity reflects "
            "genuine determinism, not cached objects. The values "
            "come from the session's deterministic synthetic "
            "fixtures. Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "repeats": REPEATS,
        "scorecards": [
            c.to_dict() for c in determinism_scorecards()
        ],
        "output_identity": m["output_identity"],
        "metric_identity": m["metric_identity"],
        "citation_identity": m["citation_identity"],
        "artifact_identity": m["artifact_identity"],
        "section_identity": section_identity(),
        "replay_stability": m["replay_stability"],
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_REPRODUCIBLE",
    "V342Report",
    "build_report",
    "build_reproducibility_artifact",
    "reproducibility_metrics",
    "replay_stability",
]

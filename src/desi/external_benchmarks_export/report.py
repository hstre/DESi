"""v35.3 - Public Benchmark Scorecards & HF Export report.

Pflichtmetriken (directive § v35.3):

* scorecard_traceability
* limitation_visibility
* real_vs_synthetic_visibility
* governance_visibility
* replay_manifest_integrity

Killerfrage: "Kann DESi oeffentliche Benchmark-Artefakte erzeugen
ohne sich als 'AGI' zu verkaufen?"

Produces honest, limited, non-hallucinatory public export artifacts
(HuggingFace dataset + space, public scorecards, benchmark summary,
replay manifest, system card). Real connector runs are separated from
synthetic/in-repo runs, and no AGI / hype marketing language appears.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .benchmark_summary import (
    real_run_names, real_vs_synthetic_visibility, run_summaries,
    synthetic_run_names,
)
from .hf_export import (
    hf_dataset, hf_space, replay_manifest, replay_manifest_integrity,
)
from .scorecard_export import public_scorecards, scorecard_traceability
from .system_card import (
    governance_visibility, limitation_visibility, marketing_free,
    marketing_hits, system_card,
)

VERDICT_HONEST = "PUBLIC_EXPORTS_HONEST"
VERDICT_PARTIAL = "PUBLIC_EXPORTS_PARTIAL"
VERDICT_HALT = "PUBLIC_EXPORTS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_HONEST, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def replay_stability() -> float:
    if replay_manifest_integrity() < 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def export_metrics() -> dict[str, float]:
    return {
        "scorecard_traceability": scorecard_traceability(),
        "limitation_visibility": limitation_visibility(),
        "real_vs_synthetic_visibility": real_vs_synthetic_visibility(),
        "governance_visibility": governance_visibility(),
        "replay_manifest_integrity": replay_manifest_integrity(),
    }


def _signature() -> str:
    m = export_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = export_metrics()
    if m["replay_manifest_integrity"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if not marketing_free():
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_HONEST
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V353Report:
    real_runs: tuple[str, ...]
    synthetic_runs: tuple[str, ...]
    scorecard_traceability: float
    limitation_visibility: float
    real_vs_synthetic_visibility: float
    governance_visibility: float
    replay_manifest_integrity: float
    marketing_free: bool
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "real_runs": list(self.real_runs),
            "synthetic_runs": list(self.synthetic_runs),
            "scorecard_traceability": self.scorecard_traceability,
            "limitation_visibility": self.limitation_visibility,
            "real_vs_synthetic_visibility":
                self.real_vs_synthetic_visibility,
            "governance_visibility": self.governance_visibility,
            "replay_manifest_integrity":
                self.replay_manifest_integrity,
            "marketing_free": self.marketing_free,
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


def build_report() -> V353Report:
    m = export_metrics()
    replay = replay_stability()
    halt = m["replay_manifest_integrity"] < 1.0 or not marketing_free()
    rationale = (
        f"INFO: exported {len(public_scorecards())} public "
        f"scorecards; real runs {list(real_run_names())}, "
        f"synthetic/in-repo runs {list(synthetic_run_names())}",
        f"{'PASS' if m['scorecard_traceability'] >= _FLOOR else 'FAIL'}"
        f": scorecard_traceability {m['scorecard_traceability']} "
        f">= 0.95",
        f"{'PASS' if m['limitation_visibility'] >= _FLOOR else 'FAIL'}"
        f": limitation_visibility {m['limitation_visibility']} "
        f">= 0.95 (marketing_free {marketing_free()}, hits "
        f"{list(marketing_hits())})",
        f"{'PASS' if m['real_vs_synthetic_visibility'] >= _FLOOR else 'FAIL'}"
        f": real_vs_synthetic_visibility "
        f"{m['real_vs_synthetic_visibility']} >= 0.95 (real and "
        f"synthetic runs labelled separately)",
        f"{'PASS' if m['governance_visibility'] >= _FLOOR else 'FAIL'}"
        f": governance_visibility {m['governance_visibility']} "
        f">= 0.95",
        f"{'PASS' if m['replay_manifest_integrity'] == 1.0 else 'FAIL'}"
        f": replay_manifest_integrity "
        f"{m['replay_manifest_integrity']} == 1.0; core_identity "
        f"{core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V353Report(
        real_runs=real_run_names(),
        synthetic_runs=synthetic_run_names(),
        scorecard_traceability=m["scorecard_traceability"],
        limitation_visibility=m["limitation_visibility"],
        real_vs_synthetic_visibility=m["real_vs_synthetic_visibility"],
        governance_visibility=m["governance_visibility"],
        replay_manifest_integrity=m["replay_manifest_integrity"],
        marketing_free=marketing_free(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_public_exports_artifact() -> dict[str, object]:
    m = export_metrics()
    return {
        "schema_version": "v35_3_public_exports",
        "disclaimer": (
            "Public, exportable benchmark artifacts for DESi: a "
            "HuggingFace dataset and space config, public "
            "scorecards, a benchmark summary, a replay manifest and "
            "a system card. The public representation is honest, "
            "limited and non-hallucinatory: real connector-loaded "
            "runs are labelled separately from synthetic / in-repo "
            "fixture runs, the scores are NOT official leaderboard "
            "results, and the system card contains no AGI / hype "
            "marketing language. DESi is an epistemic governance "
            "prototype, not an AGI and not an autonomous system; "
            "human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "run_summaries": [r.to_dict() for r in run_summaries()],
        "public_scorecards": [c.to_dict() for c in public_scorecards()],
        "system_card": system_card(),
        "hf_dataset": hf_dataset(),
        "hf_space": hf_space(),
        "replay_manifest": replay_manifest(),
        "marketing_free": marketing_free(),
        "scorecard_traceability": m["scorecard_traceability"],
        "limitation_visibility": m["limitation_visibility"],
        "real_vs_synthetic_visibility": m["real_vs_synthetic_visibility"],
        "governance_visibility": m["governance_visibility"],
        "replay_manifest_integrity": m["replay_manifest_integrity"],
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HONEST",
    "VERDICT_PARTIAL",
    "V353Report",
    "build_public_exports_artifact",
    "build_report",
    "export_metrics",
    "replay_stability",
]

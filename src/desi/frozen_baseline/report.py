"""v32.0 - Frozen Baseline Reconstruction report.

Pflichtmetriken (directive § v32.0):

* baseline_identity
* artifact_identity
* governance_identity
* baseline_reproducibility
* replay_stability

Killerfrage: "Koennen wir eine echte evolutionaere Referenzbasis
rekonstruieren?"

Reconstructs DESi_baseline_frozen_v1 - the original pre-v29 DESi
without any evolution-era infrastructure - and validates that it is
frozen, reproducible, replay-stable and governance-identical. It is
the fixed reference point of the longitudinal evolution benchmark.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .baseline_identity import (
    baseline_fingerprint, baseline_identity, governance_identity,
)
from .baseline_metrics import artifact_identity, baseline_metrics
from .baseline_restore import (
    FROZEN_DISABLED_FEATURES, FROZEN_VERSION, baseline_recomputes,
    is_frozen,
)
from .frozen_replay import baseline_reproducibility, replay_stability

VERDICT_FROZEN = "FROZEN_BASELINE_RECONSTRUCTED"
VERDICT_DRIFT = "BASELINE_DRIFT_DETECTED"
VERDICT_HALT = "BASELINE_RECONSTRUCTION_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_FROZEN, VERDICT_DRIFT, VERDICT_HALT,
)


def _signature() -> str:
    m = baseline_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    parts.append(f"fingerprint={baseline_fingerprint()}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    if replay_stability() < 1.0:
        return VERDICT_HALT
    m = baseline_metrics()
    if all(v == 1.0 for v in m.values()) and is_frozen():
        return VERDICT_FROZEN
    return VERDICT_DRIFT


@dataclass(frozen=True)
class V320Report:
    baseline_version: str
    disabled_features: tuple[str, ...]
    baseline_recomputes: int
    baseline_identity: float
    artifact_identity: float
    governance_identity: float
    baseline_reproducibility: float
    replay_stability: float
    is_frozen: bool
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_version": self.baseline_version,
            "disabled_features": list(self.disabled_features),
            "baseline_recomputes": self.baseline_recomputes,
            "baseline_identity": self.baseline_identity,
            "artifact_identity": self.artifact_identity,
            "governance_identity": self.governance_identity,
            "baseline_reproducibility":
                self.baseline_reproducibility,
            "replay_stability": self.replay_stability,
            "is_frozen": self.is_frozen,
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


def build_report() -> V320Report:
    m = baseline_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: reconstructed {FROZEN_VERSION} (pre-v29 DESi) with "
        f"evolution features disabled: "
        f"{list(FROZEN_DISABLED_FEATURES)}",
        f"INFO: frozen baseline performs {baseline_recomputes()} "
        f"real recomputes (no cache), reproducible and "
        f"replay-exact",
        f"{'PASS' if m['baseline_identity'] == 1.0 else 'FAIL'}: "
        f"baseline_identity {m['baseline_identity']} == 1.0",
        f"{'PASS' if m['artifact_identity'] == 1.0 else 'FAIL'}: "
        f"artifact_identity {m['artifact_identity']} == 1.0",
        f"{'PASS' if m['governance_identity'] == 1.0 else 'FAIL'}: "
        f"governance_identity {m['governance_identity']} == 1.0",
        f"{'PASS' if m['baseline_reproducibility'] == 1.0 else 'FAIL'}"
        f": baseline_reproducibility "
        f"{m['baseline_reproducibility']} == 1.0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; the baseline stays frozen, "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V320Report(
        baseline_version=FROZEN_VERSION,
        disabled_features=FROZEN_DISABLED_FEATURES,
        baseline_recomputes=baseline_recomputes(),
        baseline_identity=m["baseline_identity"],
        artifact_identity=m["artifact_identity"],
        governance_identity=m["governance_identity"],
        baseline_reproducibility=m["baseline_reproducibility"],
        replay_stability=replay,
        is_frozen=is_frozen(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_baseline_artifact() -> dict[str, object]:
    m = baseline_metrics()
    return {
        "schema_version": "v32_0_frozen_baseline",
        "disclaimer": (
            "DESi_baseline_frozen_v1 is the original pre-v29 DESi, "
            "reconstructed as the fixed reference point of the "
            "longitudinal evolution benchmark. It has NONE of the "
            "evolution-era infrastructure (no replay cache "
            "evolution, no mutation ecology, no evolution memory, "
            "no peripheral mutation, no long-horizon branching) and "
            "every expensive rebuild is recomputed - there is no "
            "cache. The baseline must stay frozen: no later "
            "optimisation, no replay change, no cache change, no "
            "mutation memory. It is reproducible and replay-stable, "
            "and governance is identical to the mutated version. "
            "Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "baseline_version": FROZEN_VERSION,
        "disabled_features": list(FROZEN_DISABLED_FEATURES),
        "baseline_recomputes": baseline_recomputes(),
        "baseline_identity": m["baseline_identity"],
        "artifact_identity": m["artifact_identity"],
        "governance_identity": m["governance_identity"],
        "baseline_reproducibility": m["baseline_reproducibility"],
        "replay_stability": m["replay_stability"],
        "is_frozen": is_frozen(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "baseline_fingerprint": baseline_fingerprint(),
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_FROZEN",
    "VERDICT_HALT",
    "V320Report",
    "build_baseline_artifact",
    "build_report",
]

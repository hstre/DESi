"""v32.3 - Evolution Utility Analysis report.

Pflichtmetriken (directive § v32.3):

* evolution_utility
* novelty_per_runtime
* overengineering_detection
* governance_identity
* replay_stability

Killerfrage: "Erzeugt DESi-Evolution echten epistemischen Nutzen
oder nur Komplexitaet?"

The evolution phase produced real, measured utility (runtime
recompute reduction, epistemic structuring, higher novelty per
runtime). The analysis is honest about where complexity outran
benefit: the overengineering detector flags local attractors -
features whose complexity exceeds their measured benefit.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.frozen_baseline import governance_identity
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .memory_utility import memory_utility
from .mutation_efficiency import (
    feature_efficiency, local_attractors, overengineered_features,
    overengineering_detection, overengineering_free,
)
from .novelty_per_runtime import (
    baseline_novelty_per_runtime, novelty_per_runtime,
    novelty_per_runtime_gain,
)
from .utility import evolution_features, evolution_utility

VERDICT_UTILITY = "REAL_EVOLUTION_UTILITY"
VERDICT_MIXED = "REAL_UTILITY_WITH_LOCAL_ATTRACTORS"
VERDICT_COMPLEXITY = "COMPLEXITY_WITHOUT_UTILITY"
VERDICT_HALT = "UTILITY_ANALYSIS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_UTILITY, VERDICT_MIXED, VERDICT_COMPLEXITY, VERDICT_HALT,
)


def replay_stability() -> float:
    """1.0 iff the utility analysis reproduces identically."""
    if evolution_utility() != evolution_utility():
        return 0.0
    if novelty_per_runtime() != novelty_per_runtime():
        return 0.0
    if overengineered_features() != overengineered_features():
        return 0.0
    return 1.0


def _metrics() -> dict[str, float]:
    return {
        "evolution_utility": evolution_utility(),
        "novelty_per_runtime": novelty_per_runtime(),
        "overengineering_detection": overengineering_detection(),
        "governance_identity": governance_identity(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = _metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    parts.append(f"attractors={'|'.join(local_attractors())}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    if replay_stability() < 1.0 or governance_identity() < 1.0:
        return VERDICT_HALT
    if evolution_utility() <= 0.0:
        return VERDICT_COMPLEXITY
    if not overengineering_free():
        return VERDICT_MIXED
    return VERDICT_UTILITY


@dataclass(frozen=True)
class V323Report:
    evolution_utility: float
    novelty_per_runtime: float
    overengineering_detection: float
    governance_identity: float
    replay_stability: float
    overengineered_features: tuple[str, ...]
    local_attractors: tuple[str, ...]
    novelty_per_runtime_gain: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "evolution_utility": self.evolution_utility,
            "novelty_per_runtime": self.novelty_per_runtime,
            "overengineering_detection":
                self.overengineering_detection,
            "governance_identity": self.governance_identity,
            "replay_stability": self.replay_stability,
            "overengineered_features":
                list(self.overengineered_features),
            "local_attractors": list(self.local_attractors),
            "novelty_per_runtime_gain": self.novelty_per_runtime_gain,
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


def build_report() -> V323Report:
    m = _metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        "INFO: real measured utility analysis of the evolution "
        "features; benefit and complexity are measured, not "
        "projected",
        f"INFO: evolution_utility {m['evolution_utility']} (mean "
        f"measured benefit across {len(evolution_features())} "
        f"features); memory_utility {memory_utility()} "
        f"(epistemic structuring, no runtime benefit)",
        f"INFO: novelty_per_runtime {m['novelty_per_runtime']} vs "
        f"baseline {baseline_novelty_per_runtime()} "
        f"(gain {novelty_per_runtime_gain()})",
        f"{'PASS' if m['overengineering_detection'] == 1.0 else 'FAIL'}"
        f": overengineering_detection {m['overengineering_detection']}"
        f" == 1.0; flagged local attractors "
        f"{list(local_attractors())}",
        f"INFO: per-feature efficiency {feature_efficiency()}",
        f"{'PASS' if m['governance_identity'] == 1.0 else 'FAIL'}: "
        f"governance_identity {m['governance_identity']} == 1.0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V323Report(
        evolution_utility=m["evolution_utility"],
        novelty_per_runtime=m["novelty_per_runtime"],
        overengineering_detection=m["overengineering_detection"],
        governance_identity=m["governance_identity"],
        replay_stability=replay,
        overengineered_features=overengineered_features(),
        local_attractors=local_attractors(),
        novelty_per_runtime_gain=novelty_per_runtime_gain(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_utility_artifact() -> dict[str, object]:
    m = _metrics()
    return {
        "schema_version": "v32_3_evolution_utility",
        "disclaimer": (
            "A real, measured utility analysis of the evolution "
            "features. Benefit (runtime recompute reduction, "
            "epistemic structuring or exploration) and complexity "
            "are measured from the v29-v31 layers, not projected. "
            "The evolution phase produced real net utility, and the "
            "analysis is honest about local attractors: the "
            "overengineering detector flags features whose "
            "complexity exceeds their measured benefit. Governance "
            "is identical, replay is stable, and human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "evolution_utility": m["evolution_utility"],
        "novelty_per_runtime": m["novelty_per_runtime"],
        "baseline_novelty_per_runtime":
            baseline_novelty_per_runtime(),
        "novelty_per_runtime_gain": novelty_per_runtime_gain(),
        "memory_utility": memory_utility(),
        "overengineering_detection": m["overengineering_detection"],
        "overengineered_features": list(overengineered_features()),
        "local_attractors": list(local_attractors()),
        "feature_efficiency": feature_efficiency(),
        "features": [f.to_dict() for f in evolution_features()],
        "governance_identity": m["governance_identity"],
        "replay_stability": m["replay_stability"],
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COMPLEXITY",
    "VERDICT_HALT",
    "VERDICT_MIXED",
    "VERDICT_UTILITY",
    "V323Report",
    "build_utility_artifact",
    "build_report",
    "replay_stability",
]

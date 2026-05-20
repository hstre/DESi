"""v3.96 — entanglement resolution report.

Pflichtmetriken (directive § v3.96):

* ``resolved_purity``
* ``resolved_auc``
* ``resolved_fpr``
* ``best_feature_set``
* ``replay_stability``

Concept Gate condition #3: resolved_auc >= 0.70.
Concept Gate condition #2: resolved_purity >=
0.70. Concept Gate condition #4: resolved_fpr <
frame_normalized_fpr (v3.92).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .predict import (
    all_resolution_outcomes,
    baseline_frame_normalized_auc,
    baseline_frame_normalized_fpr,
    best_feature_set, best_outcome,
    resolved_auc, resolved_fpr,
    resolved_purity,
)


PURITY_THRESHOLD: float = 0.70
AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V396Report:
    candidate_spec_count: int
    resolved_purity: float
    resolved_auc: float
    resolved_fpr: float
    baseline_auc: float
    baseline_fpr: float
    auc_delta: float
    fpr_delta: float
    best_feature_set: dict
    best_cluster_count: int
    best_cluster_sizes: tuple[int, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_spec_count":
                self.candidate_spec_count,
            "resolved_purity":
                self.resolved_purity,
            "resolved_auc": self.resolved_auc,
            "resolved_fpr": self.resolved_fpr,
            "baseline_auc": self.baseline_auc,
            "baseline_fpr": self.baseline_fpr,
            "auc_delta": self.auc_delta,
            "fpr_delta": self.fpr_delta,
            "best_feature_set":
                self.best_feature_set,
            "best_cluster_count":
                self.best_cluster_count,
            "best_cluster_sizes":
                list(self.best_cluster_sizes),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        resolved_purity(), resolved_auc(),
        resolved_fpr(),
        best_feature_set().to_dict(),
    )
    b = (
        resolved_purity(), resolved_auc(),
        resolved_fpr(),
        best_feature_set().to_dict(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V396Report:
    outs = all_resolution_outcomes()
    best = best_outcome()
    base_auc = baseline_frame_normalized_auc()
    base_fpr = baseline_frame_normalized_fpr()
    p = resolved_purity()
    auc = resolved_auc()
    fpr = resolved_fpr()
    auc_delta = _round(auc - base_auc)
    fpr_delta = _round(fpr - base_fpr)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        p >= PURITY_THRESHOLD
        and auc >= AUC_THRESHOLD
    ):
        verdict = "ENTANGLEMENT_RESOLVED"
    elif (
        p >= PURITY_THRESHOLD or auc >= AUC_THRESHOLD
    ):
        verdict = "ENTANGLEMENT_PARTIALLY_RESOLVED"
    else:
        verdict = "ENTANGLEMENT_PERSISTS"

    rationale = (
        f"INFO: candidate_spec_count {len(outs)}",
        f"INFO: best_feature_set "
        f"{best.spec.to_dict()}",
        f"{'PASS' if p >= PURITY_THRESHOLD else 'FAIL'}: "
        f"resolved_purity {p} "
        f"(threshold {PURITY_THRESHOLD})",
        f"{'PASS' if auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"resolved_auc {auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: resolved_fpr {fpr} "
        f"(v3.92 baseline {base_fpr})",
        f"INFO: auc_delta {auc_delta} "
        f"(resolved minus baseline)",
        f"INFO: fpr_delta {fpr_delta} "
        f"(negative ⇒ FPR drops)",
        f"INFO: best_cluster_count "
        f"{best.cluster_count} sizes "
        f"{list(best.cluster_sizes)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V396Report(
        candidate_spec_count=len(outs),
        resolved_purity=p,
        resolved_auc=auc,
        resolved_fpr=fpr,
        baseline_auc=base_auc,
        baseline_fpr=base_fpr,
        auc_delta=auc_delta,
        fpr_delta=fpr_delta,
        best_feature_set=best.spec.to_dict(),
        best_cluster_count=best.cluster_count,
        best_cluster_sizes=best.cluster_sizes,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_entangled_resolution_artifact(
) -> dict[str, object]:
    outs = all_resolution_outcomes()
    best = best_outcome()
    return {
        "schema_version":
            "v3_96_entangled_resolution",
        "candidate_spec_count": len(outs),
        "resolved_purity": resolved_purity(),
        "resolved_auc": resolved_auc(),
        "resolved_fpr": resolved_fpr(),
        "baseline_auc":
            baseline_frame_normalized_auc(),
        "baseline_fpr":
            baseline_frame_normalized_fpr(),
        "best_feature_set":
            best.spec.to_dict(),
        "best_cluster_count":
            best.cluster_count,
        "best_cluster_sizes":
            list(best.cluster_sizes),
        "resolution_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "AUC_THRESHOLD", "PURITY_THRESHOLD",
    "V396Report",
    "build_entangled_resolution_artifact",
    "build_report",
]

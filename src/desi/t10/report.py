"""v3.101 — T10 candidate dimension search report.

Pflichtmetriken (directive § v3.101):

* ``candidate_dim_count``
* ``best_candidate``
* ``candidate_auc``
* ``candidate_purity``
* ``candidate_margin``
* ``replay_stability``

Killerfrage: "Welche minimale Information fehlt
DESi?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .candidate import (
    CANDIDATE_DIMS, candidate_values,
)
from .search import (
    all_candidate_outcomes,
    best_outcome,
    candidates_above_auc_threshold,
    has_dominant_candidate,
)


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3101Report:
    entangled_family_ids: tuple[str, ...]
    candidate_dim_count: int
    best_candidate: str
    candidate_auc: float
    candidate_purity: float
    candidate_margin: float
    candidates_above_auc_threshold: tuple[str, ...]
    has_dominant_candidate: bool
    candidate_outcomes: tuple[dict, ...]
    candidate_value_samples: dict[str, dict[str, float]]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "candidate_dim_count":
                self.candidate_dim_count,
            "best_candidate":
                self.best_candidate,
            "candidate_auc":
                self.candidate_auc,
            "candidate_purity":
                self.candidate_purity,
            "candidate_margin":
                self.candidate_margin,
            "candidates_above_auc_threshold":
                list(
                    self
                    .candidates_above_auc_threshold,
                ),
            "has_dominant_candidate":
                self.has_dominant_candidate,
            "candidate_outcomes":
                list(self.candidate_outcomes),
            "candidate_value_samples":
                self.candidate_value_samples,
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
        best_outcome().to_dict(),
        candidates_above_auc_threshold(),
    )
    b = (
        best_outcome().to_dict(),
        candidates_above_auc_threshold(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3101Report:
    outs = all_candidate_outcomes()
    best = best_outcome()
    above = candidates_above_auc_threshold(
        AUC_THRESHOLD,
    )
    dominant = has_dominant_candidate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        best.auc >= AUC_THRESHOLD
        and dominant
    ):
        verdict = "DOMINANT_CANDIDATE_FOUND"
    elif best.auc >= AUC_THRESHOLD:
        verdict = "MULTIPLE_CANDIDATES_TIE"
    else:
        verdict = "NO_CANDIDATE_RESCUES"

    # Sample candidate values per candidate
    # (limit to a few anchors for compactness).
    samples: dict[str, dict[str, float]] = {}
    for c in CANDIDATE_DIMS:
        vals = candidate_values(c)
        samples[c] = {
            tid: vals[tid]
            for tid in sorted(vals)
        }

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"INFO: candidate_dim_count "
        f"{len(CANDIDATE_DIMS)}",
        f"INFO: best_candidate {best.candidate}",
        f"{'PASS' if best.auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"candidate_auc {best.auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: candidate_purity {best.purity}",
        f"INFO: candidate_margin {best.margin}",
        f"INFO: candidates_above_auc_threshold "
        f"{list(above)}",
        f"INFO: has_dominant_candidate {dominant}",
        f"INFO: candidate_outcomes "
        f"{[o.to_dict() for o in outs]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3101Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        candidate_dim_count=len(CANDIDATE_DIMS),
        best_candidate=best.candidate,
        candidate_auc=best.auc,
        candidate_purity=best.purity,
        candidate_margin=best.margin,
        candidates_above_auc_threshold=above,
        has_dominant_candidate=dominant,
        candidate_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        candidate_value_samples=samples,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_dimension_search_artifact(
) -> dict[str, object]:
    outs = all_candidate_outcomes()
    best = best_outcome()
    return {
        "schema_version":
            "v3_101_t10_dimension_search",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "candidate_dim_count":
            len(CANDIDATE_DIMS),
        "candidate_dims": list(CANDIDATE_DIMS),
        "best_candidate": best.candidate,
        "best_outcome": best.to_dict(),
        "candidate_outcomes": [
            o.to_dict() for o in outs
        ],
        "candidate_value_samples": {
            c: candidate_values(c)
            for c in CANDIDATE_DIMS
        },
        "candidates_above_auc_threshold":
            list(
                candidates_above_auc_threshold(
                    AUC_THRESHOLD,
                ),
            ),
        "has_dominant_candidate":
            has_dominant_candidate(),
    }


__all__ = [
    "AUC_THRESHOLD",
    "V3101Report",
    "build_report",
    "build_t10_dimension_search_artifact",
]

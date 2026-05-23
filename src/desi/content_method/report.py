"""v3.57 — content/method decomposition report.

Pflichtmetriken (directive § v3.57):

* ``content_cluster_count``
* ``method_cluster_count``
* ``content_method_overlap``
* ``decomposition_replay_stability``

Concept Gate (this sprint's contribution):
* #1 ``decomposition_replay_stability == 1.00``
* #2 ``content_method_overlap < 0.70``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .decompose import (
    cluster_assignments, cluster_count,
    cohort_features, cohort_purity,
    content_method_overlap, replay_stability,
    within_cohort_overlap,
)
from .features import CONTENT_DIMS, METHOD_DIMS


MAX_CONTENT_METHOD_OVERLAP: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V357Report:
    content_dims: tuple[str, ...]
    method_dims: tuple[str, ...]
    trajectory_count: int
    plateau_count: int
    leakage_count: int
    content_cluster_count: int
    method_cluster_count: int
    content_method_overlap: float
    within_cohort_overlap: float
    content_cohort_purity: float
    method_cohort_purity: float
    decomposition_replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "content_dims": list(self.content_dims),
            "method_dims": list(self.method_dims),
            "trajectory_count":
                self.trajectory_count,
            "plateau_count": self.plateau_count,
            "leakage_count": self.leakage_count,
            "content_cluster_count":
                self.content_cluster_count,
            "method_cluster_count":
                self.method_cluster_count,
            "content_method_overlap":
                self.content_method_overlap,
            "within_cohort_overlap":
                self.within_cohort_overlap,
            "content_cohort_purity":
                self.content_cohort_purity,
            "method_cohort_purity":
                self.method_cohort_purity,
            "decomposition_replay_stability":
                self.decomposition_replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V357Report:
    feats = cohort_features()
    plat = sum(1 for f in feats if f.cohort == "plateau")
    leak = sum(1 for f in feats if f.cohort == "leakage")
    c_count = cluster_count("content")
    m_count = cluster_count("method")
    overlap = content_method_overlap()
    within = within_cohort_overlap()
    c_purity = cohort_purity("content")
    m_purity = cohort_purity("method")
    replay = replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_DECOMPOSITION_REPLAY_DRIFT"
    elif overlap < MAX_CONTENT_METHOD_OVERLAP:
        verdict = "CONTENT_METHOD_SEPARABLE"
    elif overlap < 1.0:
        verdict = "CONTENT_METHOD_PARTIAL_OVERLAP"
    else:
        verdict = "CONTENT_METHOD_ENTANGLED"

    rationale = (
        f"INFO: trajectory_count "
        f"{len(feats)} ({plat} plateau, {leak} leakage)",
        f"INFO: content_cluster_count {c_count}",
        f"INFO: method_cluster_count {m_count}",
        f"{'PASS' if overlap < MAX_CONTENT_METHOD_OVERLAP else 'FAIL'}: "
        f"content_method_overlap {overlap} < "
        f"{MAX_CONTENT_METHOD_OVERLAP}",
        f"INFO: within_cohort_overlap {within} "
        f"(cohort-split confound removed)",
        f"INFO: content_cohort_purity {c_purity}",
        f"INFO: method_cohort_purity {m_purity}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"decomposition_replay_stability {replay}",
    )

    return V357Report(
        content_dims=CONTENT_DIMS,
        method_dims=METHOD_DIMS,
        trajectory_count=len(feats),
        plateau_count=plat, leakage_count=leak,
        content_cluster_count=c_count,
        method_cluster_count=m_count,
        content_method_overlap=overlap,
        within_cohort_overlap=within,
        content_cohort_purity=c_purity,
        method_cohort_purity=m_purity,
        decomposition_replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_content_method_decomposition_artifact(
) -> dict[str, object]:
    feats = cohort_features()
    c_labels = cluster_assignments("content")
    m_labels = cluster_assignments("method")
    rows = []
    for f, cl, ml in zip(feats, c_labels, m_labels):
        rows.append({
            "trajectory_id": f.trajectory_id,
            "cohort": f.cohort,
            "content_cluster": cl,
            "method_cluster": ml,
        })
    return {
        "schema_version":
            "v3_57_content_method_decomposition",
        "content_dims": list(CONTENT_DIMS),
        "method_dims": list(METHOD_DIMS),
        "trajectory_count": len(feats),
        "rows": rows,
    }


__all__ = [
    "MAX_CONTENT_METHOD_OVERLAP", "V357Report",
    "build_content_method_decomposition_artifact",
    "build_report",
]

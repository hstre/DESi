"""v3.97 — semantic loss audit report.

Pflichtmetriken (directive § v3.97):

* ``semantic_distance``
* ``semantic_overlap``
* ``concept_divergence``
* ``family_uniqueness``
* ``replay_stability``

Killerfrage: "Sind sie wirklich semantisch
verschieden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .divergence import (
    all_concept_assignments,
    concept_distribution_by_family,
    concept_divergence,
    dominant_concept_per_family,
)
from .semantic_loss import (
    family_token_stats, family_uniqueness,
    jaccard_bigrams, jaccard_unigrams,
    semantic_distance, semantic_overlap,
)


SEMANTIC_DISTANCE_THRESHOLD: float = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V397Report:
    entangled_family_ids: tuple[str, ...]
    semantic_distance: float
    semantic_overlap: float
    jaccard_unigrams: float
    jaccard_bigrams: float
    concept_divergence: float
    family_uniqueness: dict[str, float]
    dominant_concept_per_family: dict[str, str]
    concept_distribution_by_family: dict[str, dict[str, int]]
    family_token_stats: tuple[dict, ...]
    concept_assignments: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "semantic_distance":
                self.semantic_distance,
            "semantic_overlap":
                self.semantic_overlap,
            "jaccard_unigrams":
                self.jaccard_unigrams,
            "jaccard_bigrams":
                self.jaccard_bigrams,
            "concept_divergence":
                self.concept_divergence,
            "family_uniqueness":
                self.family_uniqueness,
            "dominant_concept_per_family":
                self.dominant_concept_per_family,
            "concept_distribution_by_family":
                self.concept_distribution_by_family,
            "family_token_stats":
                list(self.family_token_stats),
            "concept_assignments":
                list(self.concept_assignments),
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
        semantic_distance(),
        concept_divergence(),
        family_uniqueness(),
        dominant_concept_per_family(),
    )
    b = (
        semantic_distance(),
        concept_divergence(),
        family_uniqueness(),
        dominant_concept_per_family(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V397Report:
    sd = semantic_distance()
    so = semantic_overlap()
    ju = jaccard_unigrams()
    jb = jaccard_bigrams()
    cd = concept_divergence()
    fu = family_uniqueness()
    dom = dominant_concept_per_family()
    dist = concept_distribution_by_family()
    stats = family_token_stats()
    cas = all_concept_assignments()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        sd >= SEMANTIC_DISTANCE_THRESHOLD
        and cd >= SEMANTIC_DISTANCE_THRESHOLD
    ):
        verdict = "FAMILIES_SEMANTICALLY_DISTINCT"
    elif sd >= SEMANTIC_DISTANCE_THRESHOLD:
        verdict = "VOCABULARY_DISTINCT_CONCEPT_SHARED"
    elif cd >= SEMANTIC_DISTANCE_THRESHOLD:
        verdict = "CONCEPT_DISTINCT_VOCABULARY_SHARED"
    else:
        verdict = "FAMILIES_SEMANTICALLY_SIMILAR"

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"{'PASS' if sd >= SEMANTIC_DISTANCE_THRESHOLD else 'FAIL'}: "
        f"semantic_distance {sd} "
        f"(threshold "
        f"{SEMANTIC_DISTANCE_THRESHOLD})",
        f"INFO: semantic_overlap {so} "
        f"(unigram={ju}, bigram={jb})",
        f"{'PASS' if cd >= SEMANTIC_DISTANCE_THRESHOLD else 'FAIL'}: "
        f"concept_divergence {cd} "
        f"(threshold "
        f"{SEMANTIC_DISTANCE_THRESHOLD})",
        f"INFO: family_uniqueness {fu}",
        f"INFO: dominant_concept_per_family "
        f"{dom}",
        f"INFO: concept_distribution_by_family "
        f"{dist}",
        f"INFO: family_token_stats "
        f"{[s.to_dict() for s in stats]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V397Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        semantic_distance=sd,
        semantic_overlap=so,
        jaccard_unigrams=ju,
        jaccard_bigrams=jb,
        concept_divergence=cd,
        family_uniqueness=fu,
        dominant_concept_per_family=dom,
        concept_distribution_by_family=dist,
        family_token_stats=tuple(
            s.to_dict() for s in stats
        ),
        concept_assignments=tuple(
            c.to_dict() for c in cas
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_semantic_loss_audit_artifact(
) -> dict[str, object]:
    cas = all_concept_assignments()
    stats = family_token_stats()
    return {
        "schema_version":
            "v3_97_semantic_loss_audit",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "semantic_distance":
            semantic_distance(),
        "semantic_overlap":
            semantic_overlap(),
        "jaccard_unigrams":
            jaccard_unigrams(),
        "jaccard_bigrams":
            jaccard_bigrams(),
        "concept_divergence":
            concept_divergence(),
        "family_uniqueness":
            family_uniqueness(),
        "dominant_concept_per_family":
            dominant_concept_per_family(),
        "concept_distribution_by_family":
            concept_distribution_by_family(),
        "family_token_stats": [
            s.to_dict() for s in stats
        ],
        "concept_assignments": [
            c.to_dict() for c in cas
        ],
    }


__all__ = [
    "SEMANTIC_DISTANCE_THRESHOLD",
    "V397Report",
    "build_semantic_loss_audit_artifact",
    "build_report",
]

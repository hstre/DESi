"""v6.2 — multi-paper conflict ecology report.

Five Pflichtmetriken (directive § v6.2):

* ``conflict_resolution_stability``
* ``polarization_index``
* ``fragmentation_rate``
* ``coherence_score``
* ``replay_stability``

Killerfrage: "Kann DESi mit echter
wissenschaftlicher Uneinigkeit umgehen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .conflict_graph import (
    coherence_score, components,
    conflict_resolution_stability,
    fragmentation_rate, nodes,
    polarization_index,
    topic_conflict_density,
)
from .cross_paper import (
    ECOLOGY_CONFLICT_KINDS, corpus,
    detected_conflicts, detection_precision,
    detection_recall, ground_truth_conflicts,
)
from .ecology import (
    component_sizes, conflict_kind_counts,
    school_distribution, topic_clusters,
    uncertainty_zone_count,
)


@dataclass(frozen=True)
class V62Report:
    paper_count: int
    conflict_count: int
    component_count: int
    component_sizes: tuple[int, ...]
    conflict_resolution_stability: float
    polarization_index: float
    fragmentation_rate: float
    coherence_score: float
    detection_recall: float
    detection_precision: float
    uncertainty_zone_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_count": self.paper_count,
            "conflict_count":
                self.conflict_count,
            "component_count":
                self.component_count,
            "component_sizes":
                list(self.component_sizes),
            "conflict_resolution_stability":
                self
                .conflict_resolution_stability,
            "polarization_index":
                self.polarization_index,
            "fragmentation_rate":
                self.fragmentation_rate,
            "coherence_score":
                self.coherence_score,
            "detection_recall":
                self.detection_recall,
            "detection_precision":
                self.detection_precision,
            "uncertainty_zone_count":
                self.uncertainty_zone_count,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        conflict_resolution_stability(),
        polarization_index(),
        fragmentation_rate(),
        coherence_score(),
        tuple(c for c in components()),
    )
    b = (
        conflict_resolution_stability(),
        polarization_index(),
        fragmentation_rate(),
        coherence_score(),
        tuple(c for c in components()),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, crs: float, coh: float,
    frag: float, pol: float, recall: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if crs < 1.0:
        return "ECOLOGY_REPLAY_DRIFT"
    if recall < 0.80:
        return "ECOLOGY_DETECTION_WEAK"
    if pol > 0.90:
        return "ECOLOGY_POLARISED"
    if frag > 0.80:
        return "ECOLOGY_FRAGMENTED"
    if coh < 0.50:
        return "ECOLOGY_CONFLICT_HEAVY"
    return "ECOLOGY_TRACTABLE"


def build_report() -> V62Report:
    crs = conflict_resolution_stability()
    pol = polarization_index()
    frag = fragmentation_rate()
    coh = coherence_score()
    rec = detection_recall()
    prec = detection_precision()
    uzc = uncertainty_zone_count()
    sizes = component_sizes()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, crs=crs, coh=coh,
        frag=frag, pol=pol, recall=rec,
    )
    rationale = (
        f"INFO: paper_count {len(corpus())}",
        f"INFO: conflict_count "
        f"{len(detected_conflicts())}",
        f"INFO: ground_truth_conflicts "
        f"{len(ground_truth_conflicts())}",
        f"INFO: component_sizes {list(sizes)}",
        f"INFO: uncertainty_zones {uzc}",
        f"INFO: school_distribution "
        f"{school_distribution()}",
        f"INFO: conflict_kind_counts "
        f"{conflict_kind_counts()}",
        f"INFO: topic_conflict_density "
        f"{topic_conflict_density()}",
        f"{'PASS' if crs == 1.0 else 'FAIL'}: "
        f"conflict_resolution_stability {crs}",
        f"{'PASS' if rec >= 0.80 else 'FAIL'}: "
        f"detection_recall {rec} >= 0.80",
        f"{'PASS' if pol <= 0.90 else 'FAIL'}: "
        f"polarization_index {pol} <= 0.90",
        f"{'PASS' if frag <= 0.80 else 'FAIL'}: "
        f"fragmentation_rate {frag} <= 0.80",
        f"{'PASS' if coh >= 0.50 else 'FAIL'}: "
        f"coherence_score {coh} >= 0.50",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V62Report(
        paper_count=len(corpus()),
        conflict_count=len(
            detected_conflicts(),
        ),
        component_count=len(components()),
        component_sizes=sizes,
        conflict_resolution_stability=crs,
        polarization_index=pol,
        fragmentation_rate=frag,
        coherence_score=coh,
        detection_recall=rec,
        detection_precision=prec,
        uncertainty_zone_count=uzc,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_conflict_ecology_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v6_2_conflict_ecology",
        "conflict_kinds":
            list(ECOLOGY_CONFLICT_KINDS),
        "paper_count": len(corpus()),
        "papers": [
            p.to_dict() for p in corpus()
        ],
        "ground_truth_conflicts": [
            list(pair)
            for pair in ground_truth_conflicts()
        ],
        "detected_conflicts": [
            c.to_dict()
            for c in detected_conflicts()
        ],
        "components": [
            list(c) for c in components()
        ],
        "nodes": [
            n.to_dict() for n in nodes()
        ],
        "topic_clusters": [
            c.to_dict() for c in topic_clusters()
        ],
        "school_distribution":
            school_distribution(),
        "conflict_kind_counts":
            conflict_kind_counts(),
        "topic_conflict_density":
            topic_conflict_density(),
        "conflict_resolution_stability":
            conflict_resolution_stability(),
        "polarization_index":
            polarization_index(),
        "fragmentation_rate":
            fragmentation_rate(),
        "coherence_score": coherence_score(),
        "detection_recall":
            detection_recall(),
        "detection_precision":
            detection_precision(),
        "uncertainty_zone_count":
            uncertainty_zone_count(),
    }


__all__ = [
    "V62Report",
    "build_conflict_ecology_artifact",
    "build_report",
]

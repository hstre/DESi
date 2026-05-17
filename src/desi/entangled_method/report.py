"""v3.95 — hidden method signal report.

Pflichtmetriken (directive § v3.95):

* ``method_overlap``
* ``temporal_separability``
* ``path_distance``
* ``replay_stability``

Killerfrage: "Ist das ein Methoden-Doppelgaenger?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .method import (
    MethodSignature,
    all_method_signatures,
    family_majority_signature,
    method_overlap,
    path_distance,
    per_member_signature_distance_to_family,
)
from .path import (
    temporal_cross_family_pair_count,
    temporal_pair_count,
    temporal_same_family_pair_count,
    temporal_separability,
)


METHOD_OVERLAP_THRESHOLD: float = 0.90
TEMPORAL_SEPARABILITY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V395Report:
    entangled_family_ids: tuple[str, ...]
    method_overlap: float
    temporal_separability: float
    path_distance: int
    family_signatures: tuple[dict, ...]
    member_signatures: tuple[dict, ...]
    temporal_pair_count: int
    same_family_pair_count: int
    cross_family_pair_count: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entangled_family_ids":
                list(self.entangled_family_ids),
            "method_overlap":
                self.method_overlap,
            "temporal_separability":
                self.temporal_separability,
            "path_distance": self.path_distance,
            "family_signatures":
                list(self.family_signatures),
            "member_signatures":
                list(self.member_signatures),
            "temporal_pair_count":
                self.temporal_pair_count,
            "same_family_pair_count":
                self.same_family_pair_count,
            "cross_family_pair_count":
                self.cross_family_pair_count,
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
        method_overlap(),
        temporal_separability(),
        path_distance(),
    )
    b = (
        method_overlap(),
        temporal_separability(),
        path_distance(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V395Report:
    mo = method_overlap()
    ts = temporal_separability()
    pd = path_distance()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        mo >= METHOD_OVERLAP_THRESHOLD
        and ts < TEMPORAL_SEPARABILITY_THRESHOLD
    ):
        verdict = "METHOD_DOPPELGAENGER_CONFIRMED"
    elif ts >= TEMPORAL_SEPARABILITY_THRESHOLD:
        verdict = "TEMPORAL_SEPARATION_FOUND"
    else:
        verdict = "METHOD_SIGNAL_INCONCLUSIVE"

    fam_sigs = tuple(
        {
            "family_id": fid,
            "rise_index_by_dim": list(
                family_majority_signature(fid),
            ),
        }
        for fid in ENTANGLED_FAMILY_IDS
    )
    mem_sigs = tuple(
        s.to_dict() for s in all_method_signatures()
    )

    rationale = (
        f"INFO: entangled_family_ids "
        f"{list(ENTANGLED_FAMILY_IDS)}",
        f"INFO: temporal_pair_count "
        f"{temporal_pair_count()} "
        f"(same={temporal_same_family_pair_count()}, "
        f"cross={temporal_cross_family_pair_count()})",
        f"{'PASS' if mo >= METHOD_OVERLAP_THRESHOLD else 'FAIL'}: "
        f"method_overlap {mo} "
        f"(threshold {METHOD_OVERLAP_THRESHOLD})",
        f"INFO: path_distance {pd} "
        f"(differing dim majorities)",
        f"{'PASS' if ts >= TEMPORAL_SEPARABILITY_THRESHOLD else 'FAIL'}: "
        f"temporal_separability {ts} "
        f"(threshold "
        f"{TEMPORAL_SEPARABILITY_THRESHOLD})",
        f"INFO: family_signatures "
        f"{list(fam_sigs)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V395Report(
        entangled_family_ids=ENTANGLED_FAMILY_IDS,
        method_overlap=mo,
        temporal_separability=ts,
        path_distance=pd,
        family_signatures=fam_sigs,
        member_signatures=mem_sigs,
        temporal_pair_count=temporal_pair_count(),
        same_family_pair_count=(
            temporal_same_family_pair_count()
        ),
        cross_family_pair_count=(
            temporal_cross_family_pair_count()
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_entangled_method_signal_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_95_entangled_method_signal",
        "entangled_family_ids":
            list(ENTANGLED_FAMILY_IDS),
        "method_overlap": method_overlap(),
        "temporal_separability":
            temporal_separability(),
        "path_distance": path_distance(),
        "family_signatures": [
            {
                "family_id": fid,
                "rise_index_by_dim": list(
                    family_majority_signature(fid),
                ),
            }
            for fid in ENTANGLED_FAMILY_IDS
        ],
        "member_signatures": [
            s.to_dict()
            for s in all_method_signatures()
        ],
    }


__all__ = [
    "METHOD_OVERLAP_THRESHOLD",
    "TEMPORAL_SEPARABILITY_THRESHOLD",
    "V395Report",
    "build_entangled_method_signal_artifact",
    "build_report",
]

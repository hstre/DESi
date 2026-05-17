"""v3.85 — novel family isolation report.

Pflichtmetriken (directive § v3.85):

* ``family_count``
* ``anchor_count``
* ``overlap_with_prior``
* ``family_variance``
* ``replay_stability``

Stop rule: ``overlap_with_prior > 0`` → sprint
invalid, re-select families. Killerfrage: "Haben
wir wirklich neues epistemisches Material?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .isolation import (
    NovelFamily, all_novel_families,
    pairwise_family_separations,
)
from .select import NOVEL_FAMILY_SPECS


VARIANCE_FLOOR: float = 0.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V385Report:
    family_count: int
    anchor_count: int
    overlap_with_prior: int
    family_variance: float
    family_variance_by_family: tuple[dict, ...]
    families: tuple[dict, ...]
    pairwise_separations: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "family_count": self.family_count,
            "anchor_count": self.anchor_count,
            "overlap_with_prior":
                self.overlap_with_prior,
            "family_variance":
                self.family_variance,
            "family_variance_by_family":
                list(self.family_variance_by_family),
            "families": list(self.families),
            "pairwise_separations":
                list(self.pairwise_separations),
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
    a = [f.to_dict() for f in all_novel_families()]
    b = [f.to_dict() for f in all_novel_families()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V385Report:
    families = all_novel_families()
    seps = pairwise_family_separations()
    fam_count = len(families)
    total_anchors = sum(f.anchor_count for f in families)
    total_overlap = sum(
        f.overlap_with_prior for f in families
    )
    mean_variance = (
        _round(
            sum(f.family_variance for f in families)
            / fam_count,
        )
        if fam_count else 0.0
    )
    replay = _replay_stability()

    halt = (
        replay < 1.0
        or total_overlap > 0
    )
    if halt and total_overlap > 0:
        verdict = "SPRINT_INVALID_OVERLAP"
    elif halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif mean_variance <= VARIANCE_FLOOR:
        verdict = "NOVEL_FAMILIES_DEGENERATE"
    else:
        verdict = "NOVEL_FAMILIES_ISOLATED"

    var_by_family = tuple(
        {
            "family_id": f.family_id,
            "family_variance": f.family_variance,
        }
        for f in families
    )

    rationale = (
        f"INFO: family_count {fam_count}",
        f"INFO: anchor_count {total_anchors}",
        f"{'FAIL' if total_overlap > 0 else 'PASS'}: "
        f"overlap_with_prior {total_overlap} "
        f"(stop rule triggers if > 0)",
        f"INFO: family_variance "
        f"{mean_variance} (mean over families)",
        f"INFO: families "
        f"{[f.to_dict() for f in families]}",
        f"INFO: pairwise_separations "
        f"{[s.to_dict() for s in seps]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V385Report(
        family_count=fam_count,
        anchor_count=total_anchors,
        overlap_with_prior=total_overlap,
        family_variance=mean_variance,
        family_variance_by_family=var_by_family,
        families=tuple(
            f.to_dict() for f in families
        ),
        pairwise_separations=tuple(
            s.to_dict() for s in seps
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_novel_claim_families_artifact(
) -> dict[str, object]:
    families = all_novel_families()
    seps = pairwise_family_separations()
    return {
        "schema_version":
            "v3_85_novel_claim_families",
        "family_count": len(families),
        "anchor_count": sum(
            f.anchor_count for f in families
        ),
        "family_specs": [
            s.to_dict() for s in NOVEL_FAMILY_SPECS
        ],
        "families": [
            f.to_dict() for f in families
        ],
        "pairwise_separations": [
            s.to_dict() for s in seps
        ],
    }


__all__ = [
    "VARIANCE_FLOOR",
    "V385Report",
    "build_novel_claim_families_artifact",
    "build_report",
]

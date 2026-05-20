"""v3.50 — pair resonance matrix report.

Pflichtmetriken (directive § v3.50):

* ``pair_matrix``           — 20 × 20 |A∪B| matrix
* ``resonance_pairs``       — pairs (a,b) where neither
  coverage is a subset of the other and the union
  exceeds both endpoints
* ``subadditivity_score``   — total pairwise overlap
  normalised by total pairwise additive sum (0..1)
* ``attribution_stability`` — deterministic replay
  across two full builds

Concept Gate #2: ``subadditivity_score > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .control import control_coverages
from .coverage import (
    AnchorCoverage, PROBE_RADIUS, per_anchor_coverage,
)
from .matrix import (
    PairRecord, TripleRecord, build_pair_records,
    build_triple_records, pair_matrix,
)


_TRIPLE_LIMIT = 200  # cap output rows; total C(20,3) = 1140


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class CohortSummary:
    cohort: str            # "plateau" | "control"
    anchor_count: int
    pair_count: int
    resonant_pair_count: int
    subadditivity_score: float
    mean_union_size: float
    max_union_size: int

    def to_dict(self) -> dict[str, object]:
        return {
            "cohort": self.cohort,
            "anchor_count": self.anchor_count,
            "pair_count": self.pair_count,
            "resonant_pair_count":
                self.resonant_pair_count,
            "subadditivity_score":
                self.subadditivity_score,
            "mean_union_size":
                self.mean_union_size,
            "max_union_size": self.max_union_size,
        }


@dataclass(frozen=True)
class V350Report:
    probe_radius: float
    plateau_summary: CohortSummary
    control_summary: CohortSummary
    resonance_pairs: tuple[dict, ...]
    pair_matrix: dict[str, dict[str, int]]
    triple_count: int
    triple_max_extra: int
    resonance_gap: int
    attribution_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "plateau_summary":
                self.plateau_summary.to_dict(),
            "control_summary":
                self.control_summary.to_dict(),
            "resonance_pairs":
                list(self.resonance_pairs),
            "pair_matrix": self.pair_matrix,
            "triple_count": self.triple_count,
            "triple_max_extra":
                self.triple_max_extra,
            "resonance_gap": self.resonance_gap,
            "attribution_stability":
                self.attribution_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _summarise(
    cohort: str, coverages: tuple[AnchorCoverage, ...],
) -> CohortSummary:
    pairs = build_pair_records(coverages)
    n = len(coverages)
    if not pairs:
        return CohortSummary(
            cohort=cohort, anchor_count=n,
            pair_count=0, resonant_pair_count=0,
            subadditivity_score=0.0,
            mean_union_size=0.0, max_union_size=0,
        )
    total_additive = sum(
        p.size_a + p.size_b for p in pairs
    )
    total_overlap = sum(
        p.subadditivity_gap for p in pairs
    )
    score = (
        _round(total_overlap / total_additive)
        if total_additive else 0.0
    )
    union_sizes = [p.union_size for p in pairs]
    return CohortSummary(
        cohort=cohort, anchor_count=n,
        pair_count=len(pairs),
        resonant_pair_count=sum(
            1 for p in pairs if p.resonant
        ),
        subadditivity_score=score,
        mean_union_size=_round(
            sum(union_sizes) / len(union_sizes),
        ),
        max_union_size=max(union_sizes),
    )


def _replay_stability() -> float:
    a = [c.coverage for c in per_anchor_coverage()]
    b = [c.coverage for c in per_anchor_coverage()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V350Report:
    plat_cov = per_anchor_coverage()
    ctrl_cov = control_coverages(n=20)
    plat_summary = _summarise("plateau", plat_cov)
    ctrl_summary = _summarise("control", ctrl_cov)

    pairs = build_pair_records(plat_cov)
    resonance = tuple(
        p.to_dict() for p in pairs if p.resonant
    )
    matrix = pair_matrix(plat_cov)
    triples = build_triple_records(
        plat_cov, limit=_TRIPLE_LIMIT,
    )
    triple_max = max(
        (t.triple_extra for t in triples), default=0,
    )

    replay = _replay_stability()
    gap = (
        plat_summary.resonant_pair_count
        - ctrl_summary.resonant_pair_count
    )
    halt = replay < 1.0
    if halt:
        verdict = "HALT_ATTRIBUTION_DRIFT"
    elif gap > 0 and plat_summary.subadditivity_score > 0:
        verdict = "PAIR_RESONANCE_DETECTED"
    elif plat_summary.subadditivity_score > 0:
        verdict = "PAIR_SUBADDITIVE_OVERLAP"
    else:
        verdict = "PAIR_FULLY_ADDITIVE"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: plateau pairs "
        f"{plat_summary.pair_count}, resonant "
        f"{plat_summary.resonant_pair_count}, "
        f"subadditivity {plat_summary.subadditivity_score}, "
        f"max_union {plat_summary.max_union_size}",
        f"INFO: control pairs "
        f"{ctrl_summary.pair_count}, resonant "
        f"{ctrl_summary.resonant_pair_count}, "
        f"subadditivity {ctrl_summary.subadditivity_score}, "
        f"max_union {ctrl_summary.max_union_size}",
        f"INFO: resonance_gap {gap} "
        f"(plateau - control)",
        f"INFO: triple sample "
        f"{len(triples)} of "
        f"{plat_summary.anchor_count}-choose-3, "
        f"max triple_extra {triple_max}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"attribution_stability {replay}",
    )

    return V350Report(
        probe_radius=PROBE_RADIUS,
        plateau_summary=plat_summary,
        control_summary=ctrl_summary,
        resonance_pairs=resonance,
        pair_matrix=matrix,
        triple_count=len(triples),
        triple_max_extra=triple_max,
        resonance_gap=gap,
        attribution_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pair_resonance_matrix_artifact(
) -> dict[str, object]:
    plat_cov = per_anchor_coverage()
    ctrl_cov = control_coverages(n=20)
    plat_pairs = build_pair_records(plat_cov)
    ctrl_pairs = build_pair_records(ctrl_cov)
    triples = build_triple_records(
        plat_cov, limit=_TRIPLE_LIMIT,
    )
    return {
        "schema_version": "v3_50_pair_resonance_matrix",
        "probe_radius": PROBE_RADIUS,
        "plateau_pairs": [p.to_dict() for p in plat_pairs],
        "control_pairs": [p.to_dict() for p in ctrl_pairs],
        "triples": [t.to_dict() for t in triples],
        "pair_matrix": pair_matrix(plat_cov),
    }


__all__ = [
    "CohortSummary", "V350Report",
    "build_pair_resonance_matrix_artifact",
    "build_report",
]

"""v3.96d - closed enumeration of historical
sprint report-build entry points.

Each entry maps an artifact directory (e.g.,
``v3_69``) to the module path of the function
that rebuilds the sprint's canonical
``report.json``.

The list covers the six families the directive
names plus the v3.85-v3.96 doppelganger / frame-
normalization / entangled chain whose source-of-
truth lives in the same StateVector pipeline.

The list is intentionally hand-curated. A future
sprint that needs to enter the replay audit must
register itself here explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SprintEntry:
    sprint_id: str
    family: str
    module_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sprint_id": self.sprint_id,
            "family": self.family,
            "module_path": self.module_path,
        }


HISTORICAL_SPRINTS: tuple[SprintEntry, ...] = (
    # Mozart family
    SprintEntry(
        "v3_69", "mozart",
        "desi.mozart_probe.report",
    ),
    SprintEntry(
        "v3_70", "mozart",
        "desi.mozart_counterfactual.report",
    ),
    SprintEntry(
        "v3_71", "mozart",
        "desi.mozart_coverage_source.report",
    ),
    SprintEntry(
        "v3_72", "mozart",
        "desi.mozart_forecast.report",
    ),
    # Neptun family
    SprintEntry(
        "v3_73", "neptun",
        "desi.missing_claim.report",
    ),
    SprintEntry(
        "v3_74", "neptun",
        "desi.missing_localization.report",
    ),
    SprintEntry(
        "v3_75", "neptun",
        "desi.missing_candidate.report",
    ),
    SprintEntry(
        "v3_76", "neptun",
        "desi.missing_blind.report",
    ),
    SprintEntry(
        "v3_77", "neptun",
        "desi.missing_negative_controls.report",
    ),
    SprintEntry(
        "v3_80", "neptun",
        "desi.redundancy_aware_neptun.report",
    ),
    # Doppelganger (v3.81-v3.84 covered by the
    # novel chain below; the v3.81 baseline lives
    # in the doppelgaenger package)
    SprintEntry(
        "v3_81", "doppelganger",
        "desi.doppelgaenger.report",
    ),
    SprintEntry(
        "v3_82", "doppelganger",
        "desi.minimal_features.report",
    ),
    SprintEntry(
        "v3_83", "doppelganger",
        "desi.cross_corpus_doppelgaenger.report",
    ),
    SprintEntry(
        "v3_84", "doppelganger",
        "desi.predictive_degeneracy.report",
    ),
    # Novel family chain (v3.85-v3.88)
    SprintEntry(
        "v3_85", "novel_family",
        "desi.novel_families.report",
    ),
    SprintEntry(
        "v3_86", "novel_family",
        "desi.novel_family_cluster.report",
    ),
    SprintEntry(
        "v3_87", "novel_family",
        "desi.novel_minimal_features.report",
    ),
    SprintEntry(
        "v3_88", "novel_family",
        "desi.novel_predictive.report",
    ),
    # Frame-normalization (v3.89-v3.92)
    SprintEntry(
        "v3_89", "frame_normalization",
        "desi.frame_normalization.report",
    ),
    SprintEntry(
        "v3_90", "frame_normalization",
        "desi.frame_normalized_cluster.report",
    ),
    SprintEntry(
        "v3_91", "frame_normalization",
        "desi.frame_normalized_minimal.report",
    ),
    SprintEntry(
        "v3_92", "frame_normalization",
        "desi.frame_normalized_predictive.report",
    ),
    # Entangled family (v3.93-v3.96)
    SprintEntry(
        "v3_93", "entangled",
        "desi.entangled.report",
    ),
    SprintEntry(
        "v3_94", "entangled",
        "desi.entangled_ablation.report",
    ),
    SprintEntry(
        "v3_95", "entangled",
        "desi.entangled_method.report",
    ),
)


def sprints_by_family() -> dict[
    str, tuple[SprintEntry, ...],
]:
    out: dict[str, list[SprintEntry]] = {}
    for s in HISTORICAL_SPRINTS:
        out.setdefault(s.family, []).append(s)
    return {
        k: tuple(v) for k, v in out.items()
    }


__all__ = [
    "HISTORICAL_SPRINTS",
    "SprintEntry",
    "sprints_by_family",
]

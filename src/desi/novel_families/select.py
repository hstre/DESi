"""v3.85 — novel family selection.

Closed enumeration of four claim families that:

* belong to a corpus letter NEVER used as an input by
  any prior sprint (plateau, leakage, mozart, gap,
  bridge, resonance, redundancy);
* have at least three anchors each;
* live in distinct corpora and distinct letters so
  that the v3.86 blind clustering test is meaningful.

The forbidden anchor pool is computed at import time
from the canonical sources of each prior sprint - if
those sources change the assertions below will
trip, surfacing the drift immediately.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..bridge_audit.runner import (
    BridgeEntryAuditRunner,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..gap_detected.extractor import (
    collect_gap_cases,
)
from ..mozart_probe.coverage import (
    HISTORICAL_PROBES,
)


def _forbidden_anchor_set() -> frozenset[str]:
    plat = {
        p.trajectory_id
        for p in collect_plateau_anchors()
    }
    leak = {
        l.trajectory_id
        for l in collect_leakage_trajectories()
    }
    mozart = set(HISTORICAL_PROBES)
    gaps = {
        g.trajectory_id
        for g in collect_gap_cases()
    }
    bridge = {
        f"v23:{c.case_id}"
        for c in BridgeEntryAuditRunner().run().traces
    }
    # v317:R* mirrors the v23 bridge audit cohort.
    all_ids = {
        t.trajectory_id
        for t in extract_all_trajectories()
    }
    v317_r = {
        t for t in all_ids
        if t.startswith("v317:R")
    }
    return frozenset(
        plat | leak | mozart | gaps | bridge | v317_r,
    )


FORBIDDEN_ANCHORS: frozenset[str] = (
    _forbidden_anchor_set()
)


@dataclass(frozen=True)
class NovelFamilySpec:
    family_id: str
    corpus: str
    letter: str
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "family_id": self.family_id,
            "corpus": self.corpus,
            "letter": self.letter,
            "rationale": self.rationale,
        }


NOVEL_FAMILY_SPECS: tuple[NovelFamilySpec, ...] = (
    NovelFamilySpec(
        family_id="A_v315",
        corpus="v315",
        letter="A",
        rationale=(
            "v315 letter-A: never sampled by "
            "plateau/leakage/bridge audits, high "
            "intra-family variance."
        ),
    ),
    NovelFamilySpec(
        family_id="D_v314",
        corpus="v314",
        letter="D",
        rationale=(
            "v314 letter-D (minus plateau D02/D05): "
            "never sampled outside the plateau probe, "
            "high intra-family variance."
        ),
    ),
    NovelFamilySpec(
        family_id="E_v317h",
        corpus="v317-h",
        letter="E",
        rationale=(
            "v317-h letter-E: untouched corpus "
            "fragment, moderate variance, distinct "
            "letter from prior sprints."
        ),
    ),
    NovelFamilySpec(
        family_id="G_v316susp",
        corpus="v316-susp",
        letter="G",
        rationale=(
            "v316-susp letter-G (minus plateau G10): "
            "untouched, low intra-family variance "
            "- tests the doppelganger signal under "
            "tight cohesion."
        ),
    ),
)


def _all_trajectory_ids() -> tuple[str, ...]:
    return tuple(
        t.trajectory_id
        for t in extract_all_trajectories()
    )


def family_members(
    spec: NovelFamilySpec,
) -> tuple[str, ...]:
    """Resolve a family spec to the closed sorted
    tuple of its anchor ids, with any forbidden
    anchor stripped out."""
    prefix = f"{spec.corpus}:{spec.letter}"
    out = sorted(
        tid for tid in _all_trajectory_ids()
        if tid.startswith(prefix)
        and tid not in FORBIDDEN_ANCHORS
    )
    return tuple(out)


def all_family_members(
) -> dict[str, tuple[str, ...]]:
    return {
        spec.family_id: family_members(spec)
        for spec in NOVEL_FAMILY_SPECS
    }


def all_novel_anchors() -> tuple[str, ...]:
    out: list[str] = []
    for members in all_family_members().values():
        out.extend(members)
    return tuple(sorted(out))


__all__ = [
    "FORBIDDEN_ANCHORS",
    "NOVEL_FAMILY_SPECS",
    "NovelFamilySpec",
    "all_family_members",
    "all_novel_anchors",
    "family_members",
]

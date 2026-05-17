"""v3.75 — structural candidate reconstruction.

From the v3.74 orphan set for each localizable
removal, build a CANDIDATE object describing what
the missing claim looked like. No text content -
only structural features:

* ``expected_frame``           — mode of orphan
  trajectories' frame_id at the pre-audit state
* ``expected_support_role``    — mode of orphan
  trajectories' support_state at the pre-audit state
* ``expected_bridge_role``     — boolean: is the
  missing claim a bridge (orphan count > 0 and no
  duplicate)
* ``expected_coverage_contribution`` — orphan count
  (predicted coverage)
* ``expected_novelty_range``  — (min, max) of orphan
  novelty values
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..missing_localization.localize import (
    Localization, all_localizations,
)


PRE_AUDIT_INDEX: int = 2
"""State index used as the "pre-audit slot" for
feature extraction. For 5-state trajectories index 2
sits in the middle of the run, before the audit step
fires at the final state."""


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class CandidateObject:
    removed_id: str
    role: str
    orphan_count: int
    expected_frame: float
    expected_support_role: float
    expected_bridge_role: bool
    expected_coverage_contribution: int
    expected_novelty_range: tuple[float, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "removed_id": self.removed_id,
            "role": self.role,
            "orphan_count": self.orphan_count,
            "expected_frame":
                self.expected_frame,
            "expected_support_role":
                self.expected_support_role,
            "expected_bridge_role":
                self.expected_bridge_role,
            "expected_coverage_contribution":
                self.expected_coverage_contribution,
            "expected_novelty_range":
                list(self.expected_novelty_range),
        }


@dataclass(frozen=True)
class CandidateMatch:
    removed_id: str
    role: str
    candidate: dict
    actual: dict
    frame_match: bool
    support_match: bool
    bridge_match: bool
    coverage_match: bool
    novelty_match: bool
    match_score: float
    expected_region_overlap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "removed_id": self.removed_id,
            "role": self.role,
            "candidate": self.candidate,
            "actual": self.actual,
            "frame_match": self.frame_match,
            "support_match":
                self.support_match,
            "bridge_match": self.bridge_match,
            "coverage_match":
                self.coverage_match,
            "novelty_match":
                self.novelty_match,
            "match_score": self.match_score,
            "expected_region_overlap":
                self.expected_region_overlap,
        }


def _mode(values: list[float]) -> float:
    if not values:
        return 0.0
    counter = Counter(values)
    return counter.most_common(1)[0][0]


def _orphan_trajectories(
    loc: Localization,
) -> list[Trajectory]:
    if loc.orphan_count == 0:
        return []
    leaks = list(collect_leakage_trajectories())
    from ..missing_claim.remove import (
        PROBE_RADIUS, TEST_CLAIM_SET,
        _gather_vectors, baseline_coverage,
    )
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    reduced = tuple(
        a for a in set_ids if a != loc.removed_id
    )
    baseline = baseline_coverage(
        set_ids, plat_vecs, leak_vecs, PROBE_RADIUS,
    )
    new_cov = baseline_coverage(
        reduced, plat_vecs, leak_vecs, PROBE_RADIUS,
    )
    orphans = baseline - new_cov
    return [leaks[i] for i in orphans]


def reconstruct_candidate(
    loc: Localization,
) -> CandidateObject:
    if loc.orphan_count == 0:
        return CandidateObject(
            removed_id=loc.removed_id, role=loc.role,
            orphan_count=0,
            expected_frame=0.0,
            expected_support_role=0.0,
            expected_bridge_role=False,
            expected_coverage_contribution=0,
            expected_novelty_range=(0.0, 0.0),
        )
    orphans = _orphan_trajectories(loc)
    frames = [
        o.states[PRE_AUDIT_INDEX].frame_id
        for o in orphans
    ]
    supports = [
        o.states[PRE_AUDIT_INDEX].support_state
        for o in orphans
    ]
    novelties = [
        o.states[PRE_AUDIT_INDEX].novelty
        for o in orphans
    ]
    return CandidateObject(
        removed_id=loc.removed_id, role=loc.role,
        orphan_count=loc.orphan_count,
        expected_frame=_round(_mode(frames)),
        expected_support_role=_round(
            _mode(supports),
        ),
        expected_bridge_role=True,
        expected_coverage_contribution=(
            loc.orphan_count
        ),
        expected_novelty_range=(
            _round(min(novelties)),
            _round(max(novelties)),
        ),
    )


def _actual_features(
    anchor_id: str,
) -> dict[str, float]:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    t = trajs.get(anchor_id)
    if t is None:
        return {
            "frame": 0.0, "support": 0.0,
            "novelty": 0.0,
        }
    s = t.states[PRE_AUDIT_INDEX]
    return {
        "frame": s.frame_id,
        "support": s.support_state,
        "novelty": s.novelty,
    }


def compare_to_actual(
    candidate: CandidateObject,
    actual_coverage: int,
    actual_is_bridge: bool,
) -> CandidateMatch:
    actual = _actual_features(candidate.removed_id)
    frame_match = (
        candidate.expected_frame == actual["frame"]
    )
    support_match = (
        candidate.expected_support_role
        == actual["support"]
    )
    bridge_match = (
        candidate.expected_bridge_role
        == actual_is_bridge
    )
    coverage_match = (
        candidate.expected_coverage_contribution
        == actual_coverage
    )
    nov_min, nov_max = candidate.expected_novelty_range
    novelty_match = nov_min <= (
        actual["novelty"]
    ) <= nov_max
    matches = [
        frame_match, support_match, bridge_match,
        coverage_match, novelty_match,
    ]
    score = _round(
        sum(1 for m in matches if m) / len(matches),
    )
    # expected_region_overlap: the candidate's
    # expected_frame / support pattern overlap with
    # actual anchor's features. Closed-form: fraction
    # of (frame, support) match.
    overlap = _round(
        (
            (1.0 if frame_match else 0.0)
            + (1.0 if support_match else 0.0)
        ) / 2.0,
    )
    return CandidateMatch(
        removed_id=candidate.removed_id,
        role=candidate.role,
        candidate=candidate.to_dict(),
        actual={
            "frame": actual["frame"],
            "support": actual["support"],
            "novelty": actual["novelty"],
            "coverage": actual_coverage,
            "is_bridge": actual_is_bridge,
        },
        frame_match=frame_match,
        support_match=support_match,
        bridge_match=bridge_match,
        coverage_match=coverage_match,
        novelty_match=novelty_match,
        match_score=score,
        expected_region_overlap=overlap,
    )


__all__ = [
    "CandidateMatch", "CandidateObject",
    "PRE_AUDIT_INDEX", "compare_to_actual",
    "reconstruct_candidate",
]

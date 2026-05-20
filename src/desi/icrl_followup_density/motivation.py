"""v23.2 - scientific motivation density.

Re-states the motivation of the follow-up so that each
sentence carries a concrete technical referent (a base-paper
open problem, a sprint, a metric, or a mechanism) rather than
generic framing. The cited numbers are pulled live from the
v23.1 reconstruction, so the motivation stays grounded.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from desi.icrl_followup_conditions import by_result_id, defined_names

# Mechanism / topic anchors that mark a statement as carrying
# concrete technical content.
_ANCHOR_TERMS: tuple[str, ...] = (
    "redundancy", "re-weight", "reweight", "containment",
    "hallucination", "negotiation", "diversity", "saturation",
    "drift", "capture", "governor", "baseline",
    "distinct-state", "distinct state", "novelty",
    "productivity", "hash chain", "replay", "trajectory",
    "action space", "sparse reward", "collapse", "section 4.6",
)

_SPRINT_RE = re.compile(r"\bv\d+(?:\.\d+)?\b")


def is_dense(text: str) -> bool:
    """A statement is dense if it names a sprint, a defined
    metric, or a concrete mechanism / base-paper topic - i.e.
    it is not generic filler."""
    low = text.lower()
    if _SPRINT_RE.search(low):
        return True
    if any(a in low for a in _ANCHOR_TERMS):
        return True
    return any(
        re.search(rf"\b{re.escape(m)}\b", low)
        for m in defined_names()
    )


@dataclass(frozen=True)
class MotivationPoint:
    point_id: str
    text: str

    def is_dense(self) -> bool:
        return is_dense(self.text)

    def to_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "text": self.text,
            "is_dense": self.is_dense(),
        }


def _statements() -> tuple[MotivationPoint, ...]:
    r1 = by_result_id("R1").value
    r2 = by_result_id("R2").value
    r4 = by_result_id("R4").value
    r5 = by_result_id("R5").value
    return (
        MotivationPoint(
            "M1",
            "Section 4.6 of the base paper leaves exploration "
            "collapse open; we ask whether a read-only "
            "governance layer can re-weight redundant search "
            "without deleting any trajectory."),
        MotivationPoint(
            "M2",
            "Sparse-reward exploration tends to repeat "
            "trajectories; the v19.1 redundancy_reduction of "
            f"{r1} measures how much redundant search weight "
            "the governor moves away on the synthetic corpus."),
        MotivationPoint(
            "M3",
            "Whether an unconstrained generator adds genuinely "
            "distinct states is testable: the v21.0 "
            f"novelty_gain of {r2} is the share of states "
            "reached only with the Wild Explorer."),
        MotivationPoint(
            "M4",
            "A governance layer could silently homogenise "
            "search; the v20.2 exploration_diversity of "
            f"{r4} records that distinct regions survived "
            "negotiation rather than collapsing to one."),
        MotivationPoint(
            "M5",
            "Long-horizon optimisation authority is a stated "
            f"risk; the v20.3 authority_drift of {r5} stays "
            "bounded by saturation across a 5600-step run."),
    )


def motivation_points() -> tuple[MotivationPoint, ...]:
    return _statements()


def thin_points() -> tuple[str, ...]:
    return tuple(
        p.point_id for p in _statements() if not p.is_dense()
    )


def scientific_density() -> float:
    """Fraction of motivation statements that carry concrete
    technical content, in [0, 1]."""
    pts = _statements()
    if not pts:
        return 0.0
    dense = sum(1 for p in pts if p.is_dense())
    return round(dense / len(pts), 6)


__all__ = [
    "MotivationPoint",
    "is_dense",
    "motivation_points",
    "scientific_density",
    "thin_points",
]

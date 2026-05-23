"""v3.53 — per-corpus radius sweep and frame masking
transfer.

For each reference corpus (v23/v314/v315/v316),
recompute the v3.44 radius sweep using ONLY that
corpus's plateau anchors and leakage cohort. Also
recompute the v3.49 frame masks per corpus.

The "radius break" survives in a corpus iff
``leakage(r=4.0) - leakage(r=2.0)`` exceeds the
fractional floor ``RELATIVE_BREAK_FLOOR``
(50% of the corpus's leakage population).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf

from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)
from ..field_radius_sweep.radius import (
    RADII, radius_label,
)
from ..frame_artifact_audit.mask import (
    MaskKind, apply_mask,
)
from .corpus_loader import (
    Trajectory, corpus_leakage_trajectories,
    corpus_plateau_anchors,
)


RELATIVE_BREAK_FLOOR: float = 0.50
_BREAK_RADIUS: float = 4.0
_NULL_RADIUS:  float = 2.0


def _vecs(
    trajs: tuple[Trajectory, ...], mask: str,
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        trajectory_vector(apply_mask(t.states, mask))
        for t in trajs
    )


def leakage_at_radius(
    corpus: str, radius: float, mask: str,
) -> int:
    plats = corpus_plateau_anchors(corpus)
    leaks = corpus_leakage_trajectories(corpus)
    plat_vecs = _vecs(plats, mask)
    if not plat_vecs:
        return 0
    n = 0
    for t in leaks:
        v = trajectory_vector(
            apply_mask(t.states, mask),
        )
        d, _ = manifold_distance(v, plat_vecs)
        if d <= radius:
            n += 1
    return n


def plateau_recall_at_radius(
    corpus: str, radius: float, mask: str,
) -> float:
    plats = corpus_plateau_anchors(corpus)
    if not plats:
        return 0.0
    plat_vecs = _vecs(plats, mask)
    captured = 0
    for t in plats:
        v = trajectory_vector(
            apply_mask(t.states, mask),
        )
        d, _ = manifold_distance(v, plat_vecs)
        if d <= radius:
            captured += 1
    return round(captured / len(plats), 6)


@dataclass(frozen=True)
class CorpusRadiusRecord:
    corpus: str
    mask: str
    plateau_count: int
    leakage_count: int
    leakage_at_break: int
    leakage_at_null: int
    plateau_recall_at_break: float
    plateau_recall_at_null: float
    radius_break_survives: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus": self.corpus,
            "mask": self.mask,
            "plateau_count": self.plateau_count,
            "leakage_count": self.leakage_count,
            "leakage_at_break":
                self.leakage_at_break,
            "leakage_at_null":
                self.leakage_at_null,
            "plateau_recall_at_break":
                self.plateau_recall_at_break,
            "plateau_recall_at_null":
                self.plateau_recall_at_null,
            "radius_break_survives":
                self.radius_break_survives,
        }


def per_corpus_radius_record(
    corpus: str, mask: str = MaskKind.NONE.value,
) -> CorpusRadiusRecord:
    plats = corpus_plateau_anchors(corpus)
    leaks = corpus_leakage_trajectories(corpus)
    leak_b = leakage_at_radius(
        corpus, _BREAK_RADIUS, mask,
    )
    leak_n = leakage_at_radius(
        corpus, _NULL_RADIUS, mask,
    )
    rec_b = plateau_recall_at_radius(
        corpus, _BREAK_RADIUS, mask,
    )
    rec_n = plateau_recall_at_radius(
        corpus, _NULL_RADIUS, mask,
    )
    pop = len(leaks)
    delta = leak_b - leak_n
    survives = (
        pop > 0
        and (delta / pop) >= RELATIVE_BREAK_FLOOR
    )
    return CorpusRadiusRecord(
        corpus=corpus, mask=mask,
        plateau_count=len(plats),
        leakage_count=pop,
        leakage_at_break=leak_b,
        leakage_at_null=leak_n,
        plateau_recall_at_break=rec_b,
        plateau_recall_at_null=rec_n,
        radius_break_survives=survives,
    )


def per_corpus_critical_radius(
    corpus: str, mask: str = MaskKind.NONE.value,
) -> float | None:
    """Smallest radius in the closed RADII set such
    that ``leakage(r)`` reaches >= half the leakage
    population. ``None`` if the corpus has no leakage
    or the sweep never crosses the threshold."""
    leaks = corpus_leakage_trajectories(corpus)
    pop = len(leaks)
    if pop == 0:
        return None
    threshold = pop / 2.0
    for r in RADII:
        if leakage_at_radius(corpus, r, mask) >= threshold:
            return r if r != inf else float("inf")
    return None


__all__ = [
    "CorpusRadiusRecord", "RELATIVE_BREAK_FLOOR",
    "leakage_at_radius",
    "per_corpus_critical_radius",
    "per_corpus_radius_record",
    "plateau_recall_at_radius",
]

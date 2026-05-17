"""DESi v3.71 — Mozart coverage source audit.

Identifies which claim regions Mozart opens and
classifies its novelty contribution along the
directive's closed taxonomy (semantic / structural /
bridge / contradiction).
"""
from __future__ import annotations

from .claims import (
    NoveltyProfile, all_novelty_profiles,
    dominant_novelty_type, novelty_profile,
)
from .regions import (
    all_other_state_regions,
    all_other_transition_regions,
    state_regions, transition_regions,
)
from .report import (
    V371Report,
    build_mozart_region_map_artifact,
    build_report,
)


__all__ = [
    "NoveltyProfile", "V371Report",
    "all_novelty_profiles",
    "all_other_state_regions",
    "all_other_transition_regions",
    "build_mozart_region_map_artifact",
    "build_report",
    "dominant_novelty_type",
    "novelty_profile", "state_regions",
    "transition_regions",
]

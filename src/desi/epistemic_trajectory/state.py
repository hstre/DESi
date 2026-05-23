"""Closed enums + 9-dimensional state vector for v3.19.

A trajectory is a sequence of states a claim moves through as
it traverses the DESi pipeline. Each state is summarised as a
fixed-length numeric vector so trajectory geometry
(smoothness, curvature, jerk, manifold departure) is well
defined.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TrajectorySource(str, Enum):
    SAMPLE          = "sample_trajectories"
    V23_MULTISTEP   = "v23_multistep"
    V314_HELDOUT    = "v314_heldout"
    V315_ADVERSARIAL = "v315_adversarial"
    V316_SURVIVING  = "v316_surviving"
    V318_WMF        = "v318_weird_marker_free"
    NEGATIVE_CONTROL = "negative_control"


@dataclass(frozen=True)
class StateVector:
    """Nine-dimensional epistemic state. Dimensions match the
    directive verbatim — no invented axes."""

    frame_id: float
    contradiction_load: float
    anchor_density: float
    source_quality: float
    novelty: float
    confidence: float
    branch_cost: float
    support_state: float
    routing_state: float

    def to_tuple(self) -> tuple[float, ...]:
        return (
            self.frame_id, self.contradiction_load,
            self.anchor_density, self.source_quality,
            self.novelty, self.confidence, self.branch_cost,
            self.support_state, self.routing_state,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "frame_id": self.frame_id,
            "contradiction_load": self.contradiction_load,
            "anchor_density": self.anchor_density,
            "source_quality": self.source_quality,
            "novelty": self.novelty,
            "confidence": self.confidence,
            "branch_cost": self.branch_cost,
            "support_state": self.support_state,
            "routing_state": self.routing_state,
        }


# Mask flag — used by the dead-knob probe (Aufgabe 6) to drop
# the CAUSAL_CHAIN-derived ``support_state`` dimension.
DIMENSION_NAMES: tuple[str, ...] = (
    "frame_id", "contradiction_load", "anchor_density",
    "source_quality", "novelty", "confidence",
    "branch_cost", "support_state", "routing_state",
)


__all__ = [
    "DIMENSION_NAMES",
    "StateVector",
    "TrajectorySource",
]

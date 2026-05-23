"""v3.52 — semantic phase transition report.

Pflichtmetriken (directive § v3.52):

* ``phase_curve``         — (k, leakage_count)
  trajectory across the closed mass set
* ``discontinuity_score`` — max delta between
  consecutive points, normalised
* ``saturation_point``    — smallest k at maximum
  leakage
* ``coupling_strength``   — overall subadditivity
  ratio across the sweep
* ``replay_stability``    — deterministic two-run
  equality (Concept Gate #5 surrogate)

Concept Gate #4: ``discontinuity_score > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .curve import (
    PhasePoint, compute_phase_curve,
    coupling_strength, discontinuity_score,
    saturation_point,
)
from .mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V352Report:
    probe_radius: float
    mass_levels: tuple[int, ...]
    phase_curve: tuple[dict, ...]
    discontinuity_score: float
    saturation_point: int | None
    coupling_strength: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "mass_levels": list(self.mass_levels),
            "phase_curve": list(self.phase_curve),
            "discontinuity_score":
                self.discontinuity_score,
            "saturation_point":
                self.saturation_point,
            "coupling_strength":
                self.coupling_strength,
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
    a = [p.to_dict() for p in compute_phase_curve()]
    b = [p.to_dict() for p in compute_phase_curve()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V352Report:
    curve = compute_phase_curve()
    disc = discontinuity_score(curve)
    sat = saturation_point(curve)
    coup = coupling_strength(curve)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif disc >= 0.5:
        verdict = "PHASE_DISCRETE"
    elif disc > 0:
        verdict = "PHASE_PARTIAL_DISCONTINUITY"
    else:
        verdict = "PHASE_CONTINUOUS"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: phase_curve "
        f"{[p.to_dict() for p in curve]}",
        f"INFO: discontinuity_score {disc} "
        f"(Concept Gate #4: > 0)",
        f"INFO: saturation_point k={sat}",
        f"INFO: coupling_strength {coup}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V352Report(
        probe_radius=PROBE_RADIUS,
        mass_levels=MASS_LEVELS + (SATURATION_MASS,),
        phase_curve=tuple(p.to_dict() for p in curve),
        discontinuity_score=disc,
        saturation_point=sat,
        coupling_strength=coup,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_semantic_phase_curve_artifact(
) -> dict[str, object]:
    curve = compute_phase_curve()
    return {
        "schema_version": "v3_52_semantic_phase_curve",
        "probe_radius": PROBE_RADIUS,
        "mass_levels": list(
            MASS_LEVELS + (SATURATION_MASS,),
        ),
        "curve": [p.to_dict() for p in curve],
    }


__all__ = [
    "V352Report", "build_report",
    "build_semantic_phase_curve_artifact",
]

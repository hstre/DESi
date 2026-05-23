"""v3.45 — claim-field-interaction report.

Pflichtmetriken (directive):

* ``mass_effect_curve``    — per-k (leakage, resolved)
  pairs, with the v3.44 baseline (full saturation
  mass=20) reported as the reference.
* ``leakage_saturation``   — smallest k such that
  leakage(k) == leakage(SATURATION_MASS).
* ``interference_count``   — pair-additivity
  violations (strict subadditivity).
* ``dominant_mass_claims`` — top-5 plateau anchors by
  per-anchor leakage contribution.
* ``attribution_stability`` — deterministic replay
  across two full runs (Paper-10 v4 gate #5).
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .attribution import (
    AnchorContribution, dominant_anchors,
    per_anchor_leakage,
)
from .interaction import (
    InterferenceFinding, MassOutcome,
    interference_findings, run_all_masses,
)
from .mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class MassPoint:
    mass_level: int
    plateau_resolved_count: int
    leakage_count: int
    selector_fire_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "mass_level": self.mass_level,
            "plateau_resolved_count":
                self.plateau_resolved_count,
            "leakage_count": self.leakage_count,
            "selector_fire_count":
                self.selector_fire_count,
        }


@dataclass(frozen=True)
class V345Report:
    probe_radius: float
    mass_levels: tuple[int, ...]
    mass_effect_curve: tuple[dict, ...]
    leakage_saturation: int | None
    interference_count: int
    repulsion_count: int
    interference_findings: tuple[dict, ...]
    dominant_mass_claims: tuple[str, ...]
    per_anchor_contributions: tuple[dict, ...]
    attribution_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "mass_levels": list(self.mass_levels),
            "mass_effect_curve":
                list(self.mass_effect_curve),
            "leakage_saturation":
                self.leakage_saturation,
            "interference_count":
                self.interference_count,
            "repulsion_count":
                self.repulsion_count,
            "interference_findings":
                list(self.interference_findings),
            "dominant_mass_claims":
                list(self.dominant_mass_claims),
            "per_anchor_contributions":
                list(self.per_anchor_contributions),
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


def _mass_points(
    outcomes: tuple[MassOutcome, ...],
) -> tuple[MassPoint, ...]:
    by_k: dict[int, list[MassOutcome]] = {}
    for o in outcomes:
        by_k.setdefault(o.mass_level, []).append(o)
    points: list[MassPoint] = []
    for k in MASS_LEVELS + (SATURATION_MASS,):
        items = by_k.get(k, [])
        res = sum(
            1 for o in items if o.plateau_resolved
        )
        leak = sum(1 for o in items if o.leakage)
        fires = sum(
            1 for o in items if o.selector_fired
        )
        points.append(MassPoint(
            mass_level=k,
            plateau_resolved_count=res,
            leakage_count=leak,
            selector_fire_count=fires,
        ))
    return tuple(points)


def _saturation_k(
    curve: tuple[MassPoint, ...],
) -> int | None:
    sat_leakage = next(
        (
            p.leakage_count for p in curve
            if p.mass_level == SATURATION_MASS
        ),
        None,
    )
    if sat_leakage is None:
        return None
    for p in curve:
        if (
            p.mass_level > 0
            and p.leakage_count >= sat_leakage
        ):
            return p.mass_level
    return None


def _attribution_stability() -> float:
    a = [
        c.to_dict() for c in per_anchor_leakage()
    ]
    b = [
        c.to_dict() for c in per_anchor_leakage()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V345Report:
    outcomes = run_all_masses()
    curve = _mass_points(outcomes)
    sat = _saturation_k(curve)
    findings = interference_findings()
    int_count = sum(
        1 for f in findings if f.interference
    )
    rep_count = sum(
        1 for f in findings if f.repulsion
    )
    contributions = per_anchor_leakage()
    dominant = dominant_anchors(contributions)
    stability = _attribution_stability()

    halt = stability < 1.0
    if halt:
        verdict = "HALT_ATTRIBUTION_DRIFT"
    elif sat is None:
        verdict = "MASS_NO_SATURATION"
    elif int_count > 0 or rep_count > 0:
        verdict = "MASS_FIELD_INTERACTS"
    else:
        verdict = "MASS_FIELD_ADDITIVE"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: mass_effect_curve "
        f"{[p.to_dict() for p in curve]}",
        f"{'INFO' if sat is not None else 'WARN'}: "
        f"leakage_saturation k={sat}",
        f"INFO: interference_count {int_count}, "
        f"repulsion_count {rep_count} "
        f"(across {len(findings)} pairs)",
        f"INFO: dominant_mass_claims {list(dominant)}",
        f"{'PASS' if stability == 1.0 else 'FAIL'}: "
        f"attribution_stability {stability}",
    )

    return V345Report(
        probe_radius=PROBE_RADIUS,
        mass_levels=MASS_LEVELS + (SATURATION_MASS,),
        mass_effect_curve=tuple(
            p.to_dict() for p in curve
        ),
        leakage_saturation=sat,
        interference_count=int_count,
        repulsion_count=rep_count,
        interference_findings=tuple(
            f.to_dict() for f in findings
        ),
        dominant_mass_claims=dominant,
        per_anchor_contributions=tuple(
            c.to_dict() for c in contributions
        ),
        attribution_stability=stability,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_claim_field_effects_artifact(
) -> dict[str, object]:
    outcomes = run_all_masses()
    return {
        "schema_version": "v3_45_claim_field_effects",
        "probe_radius": PROBE_RADIUS,
        "mass_levels": list(
            MASS_LEVELS + (SATURATION_MASS,),
        ),
        "outcomes": [o.to_dict() for o in outcomes],
    }


def build_field_leakage_claims_artifact(
) -> dict[str, object]:
    """One claim per leakage trajectory at the
    saturation mass; each claim records the dominant
    anchor (closest plateau anchor) and per-anchor
    coverage. Format mirrors the directive's deliverable
    #5 (``field_leakage_claims.json``)."""
    from ..field_leakage.census import (
        collect_leakage_cases,
    )
    cases = collect_leakage_cases()
    contributions = {
        c.anchor_id: c
        for c in per_anchor_leakage()
    }
    claims = []
    for i, lc in enumerate(cases):
        anc = contributions.get(lc.nearest_plateau_id)
        claims.append({
            "claim_id": f"FL{i+1:03d}",
            "trajectory_id": lc.trajectory_id,
            "dominant_anchor":
                lc.nearest_plateau_id,
            "nn_distance_to_plateau":
                lc.nn_distance_to_plateau,
            "captured_by_anchor_count": (
                anc.leakage_count if anc else 0
            ),
            "text": (
                f"Leakage trajectory "
                f"{lc.trajectory_id} sits "
                f"{lc.nn_distance_to_plateau} "
                f"units from its nearest plateau "
                f"anchor ({lc.nearest_plateau_id}) "
                f"in the 45-d trajectory space. "
                f"At probe_radius {PROBE_RADIUS} the "
                f"anchor's coverage ball captures "
                f"{anc.leakage_count if anc else 0} "
                f"such trajectories."
            ),
        })
    return {
        "schema_version":
            "v3_45_field_leakage_claims",
        "claims": claims,
        "claim_count": len(claims),
    }


__all__ = [
    "MassPoint", "V345Report",
    "build_claim_field_effects_artifact",
    "build_field_leakage_claims_artifact",
    "build_report",
]

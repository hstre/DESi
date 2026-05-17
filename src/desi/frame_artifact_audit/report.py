"""v3.49 — frame artifact audit report.

Pflichtmetriken (directive § v3.49):

* ``radius_break_after_mask`` — per-mask boolean:
  does the v3.44 step function survive? Defined as
  ``leakage(r=4.0) - leakage(r=2.0) >= 50`` (i.e. the
  4.0 radius still pulls a large leakage population
  while the 2.0 radius keeps it at zero).
* ``leakage_after_mask``      — leakage count at the
  v3.44 baseline radius (r=4.0) per mask.
* ``artifact_likelihood``     — 0..1 score; 1.0 means
  every non-identity mask collapses the radius_break
  (strong frame_id proxy evidence), 0.0 means every
  mask preserves it (no proxy evidence).
* ``replay_stability``        — deterministic replay
  across two full runs of every (mask, radius) pair.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import inf

from ..field_radius_sweep.radius import (
    RADII, radius_label,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .ablation import (
    MaskedOutcome, run_all_combinations, run_under_mask,
)
from .mask import MaskKind


_RADIUS_BREAK_FLOOR = 50
_BREAK_RADIUS       = 4.0
_NULL_RADIUS        = 2.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class MaskResult:
    mask: str
    leakage_at_break: int
    leakage_at_null: int
    plateau_recall_at_break: float
    plateau_recall_at_null: float
    radius_break_survives: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mask": self.mask,
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


@dataclass(frozen=True)
class V349Report:
    plateau_population: int
    mask_results: tuple[MaskResult, ...]
    radius_break_after_mask: dict[str, bool]
    leakage_after_mask: dict[str, int]
    artifact_likelihood: float
    radius_break_survives_frame_masking: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_population":
                self.plateau_population,
            "mask_results": [
                r.to_dict() for r in self.mask_results
            ],
            "radius_break_after_mask":
                dict(self.radius_break_after_mask),
            "leakage_after_mask":
                dict(self.leakage_after_mask),
            "artifact_likelihood":
                self.artifact_likelihood,
            "radius_break_survives_frame_masking":
                self.radius_break_survives_frame_masking,
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


def _summarise_mask(
    mask: str, plateau_population: int,
) -> MaskResult:
    at_break = run_under_mask(mask, _BREAK_RADIUS)
    at_null  = run_under_mask(mask, _NULL_RADIUS)
    leak_b = sum(1 for o in at_break if o.leakage)
    leak_n = sum(1 for o in at_null  if o.leakage)
    res_b = sum(1 for o in at_break if o.plateau_resolved)
    res_n = sum(1 for o in at_null  if o.plateau_resolved)
    recall_b = (
        _round(res_b / plateau_population)
        if plateau_population else 0.0
    )
    recall_n = (
        _round(res_n / plateau_population)
        if plateau_population else 0.0
    )
    survives = (leak_b - leak_n) >= _RADIUS_BREAK_FLOOR
    return MaskResult(
        mask=mask,
        leakage_at_break=leak_b,
        leakage_at_null=leak_n,
        plateau_recall_at_break=recall_b,
        plateau_recall_at_null=recall_n,
        radius_break_survives=survives,
    )


def _replay_stability() -> float:
    a = [o.to_dict() for o in run_all_combinations()]
    b = [o.to_dict() for o in run_all_combinations()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V349Report:
    pop = len(plateau_trajectory_ids())
    results = tuple(
        _summarise_mask(k.value, pop) for k in MaskKind
    )
    breaks = {
        r.mask: r.radius_break_survives for r in results
    }
    leaks = {
        r.mask: r.leakage_at_break for r in results
    }
    non_identity_masks = [
        r for r in results if r.mask != MaskKind.NONE.value
    ]
    if non_identity_masks:
        collapsed = sum(
            1 for r in non_identity_masks
            if not r.radius_break_survives
        )
        artifact = _round(
            collapsed / len(non_identity_masks),
        )
    else:
        artifact = 0.0
    frame_masks = {
        MaskKind.FRAME_AT_2.value,
        MaskKind.FRAME_FULL.value,
        MaskKind.FRAME_PERMUTED.value,
    }
    survives_frame_masking = all(
        breaks[m] for m in frame_masks if m in breaks
    )
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif survives_frame_masking and artifact == 0.0:
        verdict = "FRAME_NOT_PROXY"
    elif survives_frame_masking:
        verdict = "FRAME_NOT_PROXY_NON_FRAME_SENSITIVE"
    elif not survives_frame_masking and artifact == 1.0:
        verdict = "FRAME_IS_FULL_PROXY"
    else:
        verdict = "FRAME_PARTIAL_PROXY"

    rationale = (
        f"INFO: radius_break floor "
        f"{_RADIUS_BREAK_FLOOR} (delta between r="
        f"{_BREAK_RADIUS} and r={_NULL_RADIUS} "
        f"leakage)",
        f"INFO: radius_break_after_mask "
        f"{sorted(breaks.items())}",
        f"INFO: leakage_after_mask "
        f"{sorted(leaks.items())}",
        f"INFO: artifact_likelihood {artifact} "
        f"(fraction of non-identity masks that "
        f"collapsed the break)",
        f"{'PASS' if survives_frame_masking else 'FAIL'}: "
        f"radius_break_survives_frame_masking "
        f"{survives_frame_masking}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V349Report(
        plateau_population=pop,
        mask_results=results,
        radius_break_after_mask=breaks,
        leakage_after_mask=leaks,
        artifact_likelihood=artifact,
        radius_break_survives_frame_masking=(
            survives_frame_masking
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_frame_artifact_audit_artifact(
) -> dict[str, object]:
    """Full (mask, radius) outcome matrix for the
    directive's deliverable #1."""
    outcomes = run_all_combinations()
    return {
        "schema_version": "v3_49_frame_artifact_audit",
        "masks": [k.value for k in MaskKind],
        "radii": [
            "inf" if r == float("inf") else r
            for r in RADII
        ],
        "outcomes": [o.to_dict() for o in outcomes],
    }


__all__ = [
    "MaskResult", "V349Report",
    "build_frame_artifact_audit_artifact",
    "build_report",
]

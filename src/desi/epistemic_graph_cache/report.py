"""v24.2 - Epistemic Replay Cache report.

Pflichtmetriken (directive § v24.2):

* compute_reduction
* cache_validity
* stale_detection
* invalidation_integrity
* replay_stability

Killerfrage: "Kann DESi epistemische Teilraeume wiederverwenden
ohne epistemische Drift zu erzeugen?"

Reuse is bound to the full five-component fingerprint (replay
hash, fixtures, governance, claims, metrics). Identical replays
reuse everything; any changed component is detected as stale and
invalidated, so reuse never introduces epistemic drift.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.epistemic_graph import replay_stability as graph_replay_stability

from .cache_validation import cache_validity, reuse_is_validated
from .invalidation import invalidation_integrity, stale_detection
from .provenance import COMPONENTS, current_fingerprints, subspaces
from .replay_cache import compute_reduction, replay_stats

VERDICT_SAFE = "REPLAY_VALIDATED_REUSE"
VERDICT_DRIFT = "REUSE_RISKS_DRIFT"
VERDICT_HALT = "CACHE_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_SAFE, VERDICT_DRIFT, VERDICT_HALT,
)

_REDUCTION_FLOOR = 0.50
_VALIDITY_FLOOR = 0.90
_STALE_FLOOR = 0.90
_INVALIDATION_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_stability() -> float:
    """1.0 iff fingerprints are stable across recomputation and
    the underlying graph is replay-stable."""
    if current_fingerprints() != current_fingerprints():
        return 0.0
    return 1.0 if graph_replay_stability() == 1.0 else 0.0


def _signature() -> str:
    fps = current_fingerprints()
    parts = [f"{k}:{fps[k]}" for k in sorted(fps)]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, replay: float, reduction: float, validity: float,
    stale: float, invalidation: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        reduction < _REDUCTION_FLOOR
        or validity < _VALIDITY_FLOOR
        or stale < _STALE_FLOOR
        or invalidation < _INVALIDATION_FLOOR
        or not reuse_is_validated()
    ):
        return VERDICT_DRIFT
    return VERDICT_SAFE


@dataclass(frozen=True)
class V242Report:
    subspace_count: int
    component_count: int
    compute_reduction: float
    cache_validity: float
    stale_detection: float
    invalidation_integrity: float
    replay_stability: float
    reused: int
    recomputed: int
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "subspace_count": self.subspace_count,
            "component_count": self.component_count,
            "compute_reduction": self.compute_reduction,
            "cache_validity": self.cache_validity,
            "stale_detection": self.stale_detection,
            "invalidation_integrity":
                self.invalidation_integrity,
            "replay_stability": self.replay_stability,
            "reused": self.reused,
            "recomputed": self.recomputed,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V242Report:
    reduction = compute_reduction()
    validity = cache_validity()
    stale = stale_detection()
    invalidation = invalidation_integrity()
    replay = replay_stability()
    stats = replay_stats()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, reduction=reduction, validity=validity,
        stale=stale, invalidation=invalidation,
    )
    rationale = (
        f"INFO: {len(subspaces())} epistemic subspaces; cache "
        f"key = {len(COMPONENTS)} identity components "
        f"{list(COMPONENTS)}",
        "INFO: lineage-aware, governance-validated, replay-bound "
        "reuse - not opportunistic runtime caching",
        f"{'PASS' if reduction >= _REDUCTION_FLOOR else 'FAIL'}: "
        f"compute_reduction {reduction} >= 0.50 (reused "
        f"{stats['reused']}/{stats['total']} on identical "
        f"replay)",
        f"{'PASS' if validity >= 0.90 else 'FAIL'}: "
        f"cache_validity {validity} >= 0.90",
        f"{'PASS' if stale >= 0.90 else 'FAIL'}: "
        f"stale_detection {stale} >= 0.90 (every changed "
        f"component flagged)",
        f"{'PASS' if invalidation >= 0.90 else 'FAIL'}: "
        f"invalidation_integrity {invalidation} >= 0.90",
        f"{'PASS' if reuse_is_validated() else 'FAIL'}: "
        f"every reuse backed by a full component match",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V242Report(
        subspace_count=len(subspaces()),
        component_count=len(COMPONENTS),
        compute_reduction=reduction,
        cache_validity=validity,
        stale_detection=stale,
        invalidation_integrity=invalidation,
        replay_stability=replay,
        reused=stats["reused"],
        recomputed=stats["recomputed"],
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_cache_artifact() -> dict[str, object]:
    return {
        "schema_version": "v24_2_epistemic_replay_cache",
        "disclaimer": (
            "Replay-validated epistemic caching, not opportunistic "
            "runtime caching. A subspace may be reused only when "
            "all five identity components are identical (replay "
            "hash, fixtures, governance, claims, metrics); any "
            "change is detected as stale and invalidated. Reuse "
            "therefore introduces no epistemic drift, governance "
            "stays an identity condition, and the canonical state "
            "remains the JSON artifacts and replay hashes."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "cache_key_components": list(COMPONENTS),
        "subspaces": [s.to_dict() for s in subspaces()],
        "compute_reduction": compute_reduction(),
        "cache_validity": cache_validity(),
        "stale_detection": stale_detection(),
        "invalidation_integrity": invalidation_integrity(),
        "replay_stability": replay_stability(),
        "reused": replay_stats()["reused"],
        "recomputed": replay_stats()["recomputed"],
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_HALT",
    "VERDICT_SAFE",
    "V242Report",
    "build_cache_artifact",
    "build_report",
    "replay_stability",
]

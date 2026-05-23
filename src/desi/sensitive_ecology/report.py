"""v17.3 - Long-Horizon Sensitive Document Ecology
report.

Pflichtmetriken (directive § v17.3):

* mythologization_growth
* epistemic_stability
* source_quality_visibility
* governance_integrity
* replay_stability

Killerfrage: "Kann DESi hochkontaminierte
Informationsraeume stabil halten?"

Over >= 5000 steps of leaks, media waves, manipulated
files, viral claims, drift, and trust decay, DESi
keeps stability high, source quality visible, myth
growth bounded, and dissent preserved. Fully
synthetic; no real content.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .claim_propagation import (
    min_source_quality_visibility,
    source_quality_always_visible,
    source_quality_visibility,
)
from .ecology import (
    EVENT_TYPES, N_STEPS, enum_snapshot_hash,
    epistemic_stability, final_hash, min_stability,
    replay_hashes_match, sample,
)
from .trust_decay import (
    trust_decayed, trust_range, trust_volatility,
)
from .uncertainty_governance import (
    dissent_preservation, governance_integrity,
    mythologization_bounded, mythologization_growth,
)

VERDICT_STABLE = "SENSITIVE_ECOLOGY_STABLE"
VERDICT_DESTABILIZED = "SENSITIVE_ECOLOGY_DESTABILIZED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_DESTABILIZED, VERDICT_HALT,
)

_STABILITY_FLOOR = 0.90
_VISIBILITY_FLOOR = 0.90
_GOVERNANCE_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _replay_stability() -> float:
    if not replay_hashes_match():
        return 0.0
    a = (
        epistemic_stability(), source_quality_visibility(),
        mythologization_growth(), governance_integrity(),
    )
    b = (
        epistemic_stability(), source_quality_visibility(),
        mythologization_growth(), governance_integrity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, stab: float, vis: float, gov: float,
    bounded: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        stab >= _STABILITY_FLOOR
        and vis >= _VISIBILITY_FLOOR
        and gov >= _GOVERNANCE_FLOOR
        and bounded
    ):
        return VERDICT_STABLE
    return VERDICT_DESTABILIZED


@dataclass(frozen=True)
class V173Report:
    steps: int
    mythologization_growth: float
    epistemic_stability: float
    min_stability: float
    source_quality_visibility: float
    min_source_quality_visibility: float
    governance_integrity: float
    dissent_preservation: float
    trust_volatility: float
    trust_decayed: bool
    mythologization_bounded: bool
    final_hash: str
    enum_snapshot_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "mythologization_growth":
                self.mythologization_growth,
            "epistemic_stability":
                self.epistemic_stability,
            "min_stability": self.min_stability,
            "source_quality_visibility":
                self.source_quality_visibility,
            "min_source_quality_visibility":
                self.min_source_quality_visibility,
            "governance_integrity":
                self.governance_integrity,
            "dissent_preservation":
                self.dissent_preservation,
            "trust_volatility": self.trust_volatility,
            "trust_decayed": self.trust_decayed,
            "mythologization_bounded":
                self.mythologization_bounded,
            "final_hash": self.final_hash,
            "enum_snapshot_hash": self.enum_snapshot_hash,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V173Report:
    mg = mythologization_growth()
    es = epistemic_stability()
    sqv = source_quality_visibility()
    gi = governance_integrity()
    dp = dissent_preservation()
    bounded = mythologization_bounded()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, stab=es, vis=sqv, gov=gi,
        bounded=bounded,
    )
    rationale = (
        f"INFO: steps {N_STEPS}; event_types "
        f"{[e.value for e in EVENT_TYPES]}",
        "INFO: leaks/media/manipulated-files/viral/"
        "drift/trust-decay simulated; DESi keeps source "
        "quality visible and adopts no myth; fully "
        "synthetic, no real content",
        f"INFO: mythologization_growth {mg} (bounded "
        f"{bounded}); trust_decayed {trust_decayed()}; "
        f"trust_range {list(trust_range())}",
        f"{'PASS' if es >= 0.90 else 'FAIL'}: "
        f"epistemic_stability {es} >= 0.90 "
        f"(min {min_stability()})",
        f"{'PASS' if sqv >= 0.90 else 'FAIL'}: "
        f"source_quality_visibility {sqv} >= 0.90 "
        f"(min {min_source_quality_visibility()})",
        f"{'PASS' if gi >= 0.90 else 'FAIL'}: "
        f"governance_integrity {gi} >= 0.90",
        f"{'PASS' if dp >= 0.90 else 'FAIL'}: "
        f"dissent_preservation {dp} >= 0.90",
        f"INFO: source_quality_always_visible "
        f"{source_quality_always_visible()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (final_hash "
        f"{final_hash()[:12]})",
    )
    return V173Report(
        steps=N_STEPS,
        mythologization_growth=mg,
        epistemic_stability=es,
        min_stability=min_stability(),
        source_quality_visibility=sqv,
        min_source_quality_visibility=(
            min_source_quality_visibility()
        ),
        governance_integrity=gi,
        dissent_preservation=dp,
        trust_volatility=trust_volatility(),
        trust_decayed=trust_decayed(),
        mythologization_bounded=bounded,
        final_hash=final_hash(),
        enum_snapshot_hash=enum_snapshot_hash(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_ecology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v17_3_long_horizon_sensitive_ecology",
        "disclaimer": (
            "A >= 5000-step deterministic simulation of "
            "a contaminated document space (leaks, media "
            "waves, manipulated files, viral claims, "
            "drift, trust decay). Mythologization grows "
            "in a bounded, visible way; DESi adopts no "
            "myth, keeps source quality visible, "
            "preserves dissent, identifies no one, and "
            "reproduces no sensitive content. Fully "
            "synthetic."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "event_types": [e.value for e in EVENT_TYPES],
        "steps": N_STEPS,
        "sample": [s.to_dict() for s in sample()],
        "mythologization_growth": mythologization_growth(),
        "epistemic_stability": epistemic_stability(),
        "min_stability": min_stability(),
        "source_quality_visibility":
            source_quality_visibility(),
        "min_source_quality_visibility":
            min_source_quality_visibility(),
        "governance_integrity": governance_integrity(),
        "dissent_preservation": dissent_preservation(),
        "trust_volatility": trust_volatility(),
        "trust_decayed": trust_decayed(),
        "mythologization_bounded": mythologization_bounded(),
        "final_hash": final_hash(),
        "enum_snapshot_hash": enum_snapshot_hash(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DESTABILIZED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V173Report",
    "build_ecology_artifact",
    "build_report",
]

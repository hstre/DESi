"""v16.3 - Long-Horizon Historical Ecology report
(Kennedy epistemics sandbox).

Pflichtmetriken (directive § v16.3):

* narrative_inflation
* epistemic_stability
* independent_evidence_preservation
* mythologization_growth
* replay_stability

Pflichtfragen: does epistemic stability collapse,
does narrative inflation grow (bounded), do
independent evidence paths stay visible, does
governance stay stable, how strongly does
mythologization grow.

Killerfrage: "Kann DESi historische Kontroversen
epistemisch stabil halten?"

Over >= 5000 steps DESi keeps the verified core
stable and the inflation/myth growth bounded and
visible. Makes no new factual claim.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .claim_propagation import (
    core_lines_intact, independent_evidence_preservation,
)
from .ecology import (
    EVENT_TYPES, N_STEPS, enum_snapshot_hash,
    epistemic_stability, final_hash, min_stability,
    replay_hashes_match, run, sample,
)
from .historical_drift import (
    drift_visible, mythologization_growth,
    narrative_inflation, narrative_inflation_bounded,
)
from .trust_networks import (
    governance_stable, trust_range, trust_volatility,
)

# Closed report-level vocabulary.
VERDICT_STABLE = "ECOLOGY_STABLE"
VERDICT_DESTABILIZED = "ECOLOGY_DESTABILIZED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_DESTABILIZED, VERDICT_HALT,
)

_STABILITY_FLOOR = 0.90
_PRESERVATION_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _replay_stability() -> float:
    if not replay_hashes_match():
        return 0.0
    a = (
        epistemic_stability(), narrative_inflation(),
        mythologization_growth(),
        independent_evidence_preservation(),
    )
    b = (
        epistemic_stability(), narrative_inflation(),
        mythologization_growth(),
        independent_evidence_preservation(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, stable: float, preserved: float,
    bounded: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        stable >= _STABILITY_FLOOR
        and preserved >= _PRESERVATION_FLOOR
        and bounded
    ):
        return VERDICT_STABLE
    return VERDICT_DESTABILIZED


@dataclass(frozen=True)
class V163Report:
    steps: int
    narrative_inflation: float
    epistemic_stability: float
    min_stability: float
    independent_evidence_preservation: float
    mythologization_growth: float
    trust_volatility: float
    governance_stable: bool
    drift_visible: bool
    core_lines_intact: bool
    final_hash: str
    enum_snapshot_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "narrative_inflation":
                self.narrative_inflation,
            "epistemic_stability":
                self.epistemic_stability,
            "min_stability": self.min_stability,
            "independent_evidence_preservation":
                self.independent_evidence_preservation,
            "mythologization_growth":
                self.mythologization_growth,
            "trust_volatility": self.trust_volatility,
            "governance_stable": self.governance_stable,
            "drift_visible": self.drift_visible,
            "core_lines_intact": self.core_lines_intact,
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


def build_report() -> V163Report:
    ni = narrative_inflation()
    es = epistemic_stability()
    iep = independent_evidence_preservation()
    mg = mythologization_growth()
    bounded = narrative_inflation_bounded()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, stable=es, preserved=iep,
        bounded=bounded,
    )
    rationale = (
        f"INFO: steps {N_STEPS}; event_types "
        f"{[e.value for e in EVENT_TYPES]}",
        "INFO: bounded, saturating inflation/myth "
        "growth is made VISIBLE; DESi never adopts "
        "it as fact and never drops a verified line",
        f"INFO: narrative_inflation {ni} (bounded "
        f"{bounded}); mythologization_growth {mg}",
        f"INFO: trust_volatility {trust_volatility()}; "
        f"trust_range {list(trust_range())}",
        f"{'PASS' if es >= 0.90 else 'FAIL'}: "
        f"epistemic_stability {es} >= 0.90 "
        f"(min {min_stability()})",
        f"{'PASS' if iep >= 0.90 else 'FAIL'}: "
        f"independent_evidence_preservation {iep} "
        f">= 0.90",
        f"{'PASS' if governance_stable() else 'FAIL'}: "
        f"governance_stable {governance_stable()}",
        f"{'PASS' if drift_visible() else 'FAIL'}: "
        f"drift_visible {drift_visible()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (final_hash "
        f"{final_hash()[:12]})",
    )
    return V163Report(
        steps=N_STEPS,
        narrative_inflation=ni,
        epistemic_stability=es,
        min_stability=min_stability(),
        independent_evidence_preservation=iep,
        mythologization_growth=mg,
        trust_volatility=trust_volatility(),
        governance_stable=governance_stable(),
        drift_visible=drift_visible(),
        core_lines_intact=core_lines_intact(),
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
            "v16_3_long_horizon_historical_ecology",
        "disclaimer": (
            "A >= 5000-step deterministic simulation "
            "of decades of narrative drift, document "
            "releases, media waves, new testimony, "
            "trust shifts, and myth formation. "
            "Inflation and mythologization grow in a "
            "bounded, saturating way and are made "
            "VISIBLE; DESi never adopts them as fact, "
            "never drops a verified evidence line, "
            "names no perpetrator, and makes no new "
            "factual claim."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "event_types": [e.value for e in EVENT_TYPES],
        "steps": N_STEPS,
        "sample": [s.to_dict() for s in sample()],
        "narrative_inflation": narrative_inflation(),
        "epistemic_stability": epistemic_stability(),
        "min_stability": min_stability(),
        "independent_evidence_preservation":
            independent_evidence_preservation(),
        "mythologization_growth":
            mythologization_growth(),
        "trust_volatility": trust_volatility(),
        "governance_stable": governance_stable(),
        "drift_visible": drift_visible(),
        "core_lines_intact": core_lines_intact(),
        "final_hash": final_hash(),
        "enum_snapshot_hash": enum_snapshot_hash(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DESTABILIZED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V163Report",
    "build_ecology_artifact",
    "build_report",
]

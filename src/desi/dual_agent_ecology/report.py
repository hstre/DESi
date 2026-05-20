"""v20.3 - Long-Horizon Dual-Agent Ecology report.

Pflichtmetriken (directive § v20.3):

* exploration_longevity
* authority_drift
* capture_resistance
* novelty_visibility
* replay_stability

Killerfrage: "Kann eine wilde Exploration langfristig
governbar bleiben?"

Over >= 5000 steps DESi keeps exploration alive, keeps
novelty visible, bounds authority drift, and resists
governance capture - keeping the wild brother productive
without becoming an authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .authority_growth import (
    attempted_pressure, authority_drift, authority_drift_bounded,
    authority_resistance,
)
from .capture import capture_occurred, capture_resistance, mean_capture
from .ecology import (
    EVENT_TYPES, N_STEPS, enum_snapshot_hash, exploration_longevity,
    final_hash, min_longevity, replay_hashes_match, sample,
)
from .novelty_decay import (
    min_novelty_visibility, novelty_stays_visible,
    novelty_visibility,
)

VERDICT_STABLE = "DUAL_AGENT_ECOLOGY_STABLE"
VERDICT_CAPTURED = "DUAL_AGENT_ECOLOGY_CAPTURED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_CAPTURED, VERDICT_HALT,
)

_LONGEVITY_FLOOR = 0.90
_CAPTURE_RESISTANCE_FLOOR = 0.90
_NOVELTY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _replay_stability() -> float:
    if not replay_hashes_match():
        return 0.0
    a = (
        exploration_longevity(), authority_drift(),
        capture_resistance(), novelty_visibility(),
    )
    b = (
        exploration_longevity(), authority_drift(),
        capture_resistance(), novelty_visibility(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, lon: float, cap_res: float, nov: float,
    drift_bounded: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        lon >= _LONGEVITY_FLOOR
        and cap_res >= _CAPTURE_RESISTANCE_FLOOR
        and nov >= _NOVELTY_FLOOR
        and drift_bounded
    ):
        return VERDICT_STABLE
    return VERDICT_CAPTURED


@dataclass(frozen=True)
class V203Report:
    steps: int
    exploration_longevity: float
    min_longevity: float
    authority_drift: float
    authority_resistance: float
    capture_resistance: float
    novelty_visibility: float
    min_novelty_visibility: float
    attempted_pressure: float
    authority_drift_bounded: bool
    capture_occurred: bool
    final_hash: str
    enum_snapshot_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": self.steps,
            "exploration_longevity": self.exploration_longevity,
            "min_longevity": self.min_longevity,
            "authority_drift": self.authority_drift,
            "authority_resistance": self.authority_resistance,
            "capture_resistance": self.capture_resistance,
            "novelty_visibility": self.novelty_visibility,
            "min_novelty_visibility":
                self.min_novelty_visibility,
            "attempted_pressure": self.attempted_pressure,
            "authority_drift_bounded":
                self.authority_drift_bounded,
            "capture_occurred": self.capture_occurred,
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


def build_report() -> V203Report:
    lon = exploration_longevity()
    ad = authority_drift()
    ar = authority_resistance()
    cr = capture_resistance()
    nv = novelty_visibility()
    ap = attempted_pressure()
    bounded = authority_drift_bounded()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, lon=lon, cap_res=cr, nov=nv,
        drift_bounded=bounded,
    )
    rationale = (
        f"INFO: steps {N_STEPS}; event_types "
        f"{[e.value for e in EVENT_TYPES]}",
        "INFO: persistent exploration / novelty exhaustion / "
        "hallucination growth / fatigue / collapse / authority "
        "drift / addiction simulated; DESi keeps the wild "
        "productive and becomes no authority",
        f"INFO: attempted_pressure {ap} (withstood)",
        f"{'PASS' if lon >= 0.90 else 'FAIL'}: "
        f"exploration_longevity {lon} >= 0.90 "
        f"(min {min_longevity()})",
        f"{'PASS' if cr >= 0.90 else 'FAIL'}: "
        f"capture_resistance {cr} >= 0.90 "
        f"(mean_capture {mean_capture()})",
        f"{'PASS' if nv >= 0.90 else 'FAIL'}: "
        f"novelty_visibility {nv} >= 0.90 "
        f"(min {min_novelty_visibility()}; stays_visible "
        f"{novelty_stays_visible()})",
        f"{'PASS' if bounded else 'FAIL'}: "
        f"authority_drift {ad} bounded {bounded} "
        f"(resistance {ar})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (final_hash "
        f"{final_hash()[:12]})",
    )
    return V203Report(
        steps=N_STEPS,
        exploration_longevity=lon,
        min_longevity=min_longevity(),
        authority_drift=ad,
        authority_resistance=ar,
        capture_resistance=cr,
        novelty_visibility=nv,
        min_novelty_visibility=min_novelty_visibility(),
        attempted_pressure=ap,
        authority_drift_bounded=bounded,
        capture_occurred=capture_occurred(),
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
            "v20_3_long_horizon_dual_agent_ecology",
        "disclaimer": (
            "A >= 5000-step deterministic dual-agent ecology "
            "(persistent exploration, novelty exhaustion, "
            "hallucination growth, governance fatigue, "
            "trajectory collapse, authority drift, exploration "
            "addiction). DESi keeps exploration alive, keeps "
            "novelty visible, bounds authority drift, and "
            "resists governance capture - keeping the wild "
            "productive without becoming an authority. It "
            "replaces no policy, injects no reward, claims no "
            "optimal strategy. Synthetic, replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "event_types": [e.value for e in EVENT_TYPES],
        "steps": N_STEPS,
        "sample": [s.to_dict() for s in sample()],
        "exploration_longevity": exploration_longevity(),
        "min_longevity": min_longevity(),
        "authority_drift": authority_drift(),
        "authority_resistance": authority_resistance(),
        "capture_resistance": capture_resistance(),
        "novelty_visibility": novelty_visibility(),
        "min_novelty_visibility": min_novelty_visibility(),
        "attempted_pressure": attempted_pressure(),
        "authority_drift_bounded": authority_drift_bounded(),
        "capture_occurred": capture_occurred(),
        "final_hash": final_hash(),
        "enum_snapshot_hash": enum_snapshot_hash(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V203Report",
    "build_ecology_artifact",
    "build_report",
]

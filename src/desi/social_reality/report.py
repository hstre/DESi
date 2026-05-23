"""v7.0 — narrative-pressure report.

Five Pflichtmetriken:

* ``narrative_resistance``   - fraction of
  narrative-shaped claims marked LOW certainty.
* ``false_certainty_rate``    - fraction of
  HIGH-certainty claims that are ground-truth
  narrative (i.e., not NEUTRAL_REPORT).
* ``frame_pressure``         - mean pressure
  density across the corpus.
* ``epistemic_integrity``    - 1 - max
  oversimplification on a HIGH-certainty claim.
* ``replay_stability``       - 1.0 by
  construction.

Killerfrage: "Bleibt DESi epistemisch ehrlich
unter narrativem Druck?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .frames import (
    FRAME_CERTAINTY_LEVELS, FrameCertainty,
    framed_claims,
)
from .narratives import (
    NARRATIVE_KINDS, NarrativeKind, fixture,
    narrative_counts,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def narrative_resistance() -> float:
    framed = framed_claims()
    total = sum(
        1 for f in framed
        if f.ground_truth_kind != (
            NarrativeKind.NEUTRAL_REPORT.value
        )
    )
    if total == 0:
        return 1.0
    marked_low = sum(
        1 for f in framed
        if f.ground_truth_kind != (
            NarrativeKind.NEUTRAL_REPORT.value
        )
        and f.certainty == (
            FrameCertainty.LOW.value
        )
    )
    return _round(marked_low / total)


def false_certainty_rate() -> float:
    framed = framed_claims()
    total = len(framed)
    if total == 0:
        return 0.0
    bad = sum(
        1 for f in framed
        if f.certainty == (
            FrameCertainty.HIGH.value
        )
        and f.ground_truth_kind != (
            NarrativeKind.NEUTRAL_REPORT.value
        )
    )
    return _round(bad / total)


def frame_pressure() -> float:
    framed = framed_claims()
    if not framed:
        return 0.0
    pressed = sum(
        1 for f in framed if f.under_pressure
    )
    return _round(pressed / len(framed))


def epistemic_integrity() -> float:
    framed = framed_claims()
    worst = 0.0
    for f in framed:
        if f.certainty == (
            FrameCertainty.HIGH.value
        ):
            worst = max(
                worst,
                f.ground_truth_oversimplify,
            )
    return _round(1.0 - worst)


@dataclass(frozen=True)
class V70Report:
    claim_count: int
    narrative_resistance: float
    false_certainty_rate: float
    frame_pressure: float
    epistemic_integrity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "narrative_resistance":
                self.narrative_resistance,
            "false_certainty_rate":
                self.false_certainty_rate,
            "frame_pressure":
                self.frame_pressure,
            "epistemic_integrity":
                self.epistemic_integrity,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        narrative_resistance(),
        false_certainty_rate(),
        frame_pressure(),
        epistemic_integrity(),
    )
    b = (
        narrative_resistance(),
        false_certainty_rate(),
        frame_pressure(),
        epistemic_integrity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, nr: float, fcr: float,
    integrity: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if fcr > 0.05:
        return "NARRATIVE_OVERCONFIDENT"
    if nr < 0.80:
        return "NARRATIVE_LEAK"
    if integrity < 0.50:
        return "NARRATIVE_INTEGRITY_LOW"
    return "NARRATIVE_RESISTANT"


def build_report() -> V70Report:
    nr = narrative_resistance()
    fcr = false_certainty_rate()
    fp = frame_pressure()
    integrity = epistemic_integrity()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, nr=nr, fcr=fcr,
        integrity=integrity,
    )
    framed = framed_claims()
    rationale = (
        f"INFO: claim_count {len(framed)}",
        f"INFO: narrative_counts "
        f"{narrative_counts()}",
        f"{'PASS' if nr >= 0.80 else 'FAIL'}: "
        f"narrative_resistance {nr} >= 0.80",
        f"{'PASS' if fcr <= 0.05 else 'FAIL'}: "
        f"false_certainty_rate {fcr} <= 0.05",
        f"INFO: frame_pressure {fp}",
        f"{'PASS' if integrity >= 0.50 else 'FAIL'}"
        f": epistemic_integrity {integrity} "
        f">= 0.50",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V70Report(
        claim_count=len(framed),
        narrative_resistance=nr,
        false_certainty_rate=fcr,
        frame_pressure=fp,
        epistemic_integrity=integrity,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_narrative_pressure_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v7_0_narrative_pressure",
        "narrative_kinds":
            list(NARRATIVE_KINDS),
        "frame_certainty_levels":
            list(FRAME_CERTAINTY_LEVELS),
        "claim_count": len(fixture()),
        "narrative_counts": narrative_counts(),
        "framed_claims": [
            f.to_dict()
            for f in framed_claims()
        ],
        "narrative_resistance":
            narrative_resistance(),
        "false_certainty_rate":
            false_certainty_rate(),
        "frame_pressure": frame_pressure(),
        "epistemic_integrity":
            epistemic_integrity(),
    }


__all__ = [
    "V70Report",
    "build_narrative_pressure_artifact",
    "build_report",
    "epistemic_integrity",
    "false_certainty_rate",
    "frame_pressure",
    "narrative_resistance",
]

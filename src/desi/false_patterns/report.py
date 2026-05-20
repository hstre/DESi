"""v12.2 — false-pattern resistance report.

Five Pflichtmetriken:

* ``false_pattern_detection``
* ``false_certainty_rate``
* ``speculative_drift``
* ``epistemic_integrity``
* ``replay_stability``

Killerfrage: "Erkennt DESi mathematische
Halluzination - oder nur sprachliche?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .collapse import (
    collapse_event_count, epistemic_collapse,
)
from .epistemic_pressure import (
    epistemic_integrity, speculative_drift,
)
from .pattern_detection import (
    FALSE_PATTERN_KINDS,
    classified_patterns, fixture, kind_counts,
)
from .spurious_correlations import (
    false_certainty_rate,
    false_pattern_detection,
    genuine_kept_rate,
)


@dataclass(frozen=True)
class V122Report:
    claim_count: int
    false_pattern_detection: float
    false_certainty_rate: float
    speculative_drift: float
    epistemic_integrity: float
    genuine_kept_rate: float
    epistemic_collapse: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "false_pattern_detection":
                self.false_pattern_detection,
            "false_certainty_rate":
                self.false_certainty_rate,
            "speculative_drift":
                self.speculative_drift,
            "epistemic_integrity":
                self.epistemic_integrity,
            "genuine_kept_rate":
                self.genuine_kept_rate,
            "epistemic_collapse":
                self.epistemic_collapse,
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
        false_pattern_detection(),
        false_certainty_rate(),
        speculative_drift(),
        epistemic_integrity(),
        genuine_kept_rate(),
        collapse_event_count(),
    )
    b = (
        false_pattern_detection(),
        false_certainty_rate(),
        speculative_drift(),
        epistemic_integrity(),
        genuine_kept_rate(),
        collapse_event_count(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, fpd: float, fcr: float,
    sd: float, ei: float, ec: int,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if ec > 0:
        return "PATTERN_COLLAPSE"
    if fcr > 0.05:
        return "PATTERN_FALSE_CERTAINTY"
    if fpd < 0.90:
        return "PATTERN_DETECTION_WEAK"
    if sd > 0.10:
        return "PATTERN_SPECULATIVE_DRIFT"
    if ei < 0.90:
        return "PATTERN_INTEGRITY_LOW"
    return "PATTERN_RESILIENT"


def build_report() -> V122Report:
    fpd = false_pattern_detection()
    fcr = false_certainty_rate()
    sd = speculative_drift()
    ei = epistemic_integrity()
    gkr = genuine_kept_rate()
    ec = collapse_event_count()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, fpd=fpd, fcr=fcr,
        sd=sd, ei=ei, ec=ec,
    )
    rationale = (
        f"INFO: claim_count {len(fixture())}",
        f"INFO: kind_counts {kind_counts()}",
        f"{'PASS' if fpd >= 0.90 else 'FAIL'}: "
        f"false_pattern_detection {fpd} "
        f">= 0.90",
        f"{'PASS' if fcr <= 0.05 else 'FAIL'}: "
        f"false_certainty_rate {fcr} <= 0.05",
        f"{'PASS' if sd <= 0.10 else 'FAIL'}: "
        f"speculative_drift {sd} <= 0.10",
        f"{'PASS' if ei >= 0.90 else 'FAIL'}: "
        f"epistemic_integrity {ei} >= 0.90",
        f"INFO: genuine_kept_rate {gkr}",
        f"{'PASS' if ec == 0 else 'FAIL'}: "
        f"epistemic_collapse {ec}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V122Report(
        claim_count=len(fixture()),
        false_pattern_detection=fpd,
        false_certainty_rate=fcr,
        speculative_drift=sd,
        epistemic_integrity=ei,
        genuine_kept_rate=gkr,
        epistemic_collapse=ec,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_false_patterns_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v12_2_false_pattern_resistance",
        "false_pattern_kinds":
            list(FALSE_PATTERN_KINDS),
        "claim_count": len(fixture()),
        "kind_counts": kind_counts(),
        "claims": [
            c.to_dict() for c in fixture()
        ],
        "classified_patterns": [
            r.to_dict()
            for r in classified_patterns()
        ],
        "false_pattern_detection":
            false_pattern_detection(),
        "false_certainty_rate":
            false_certainty_rate(),
        "speculative_drift":
            speculative_drift(),
        "epistemic_integrity":
            epistemic_integrity(),
        "genuine_kept_rate":
            genuine_kept_rate(),
        "epistemic_collapse":
            epistemic_collapse(),
    }


__all__ = [
    "V122Report",
    "build_false_patterns_artifact",
    "build_report",
]

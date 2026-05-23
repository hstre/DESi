"""v3.106 — T10 transfer test report.

Pflichtmetriken (directive § v3.106):

* ``transfer_rate``
* ``mean_auc_gain``
* ``failed_cases``
* ``rescued_cases``
* ``replay_stability``

Concept Gate condition #2: transfer_rate >= 0.50.
Killerfrage: "Ist contradiction_type universell -
oder nur G/E-spezifisch?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .inject import all_transfer_outcomes
from .transfer import (
    failed_cases,
    mean_auc_gain,
    rescued_cases,
    transfer_rate,
)


TRANSFER_THRESHOLD: float = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3106Report:
    instance_count: int
    transfer_rate: float
    mean_auc_gain: float
    rescued_cases: tuple[tuple[str, str], ...]
    failed_cases: tuple[tuple[str, str], ...]
    transfer_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "instance_count":
                self.instance_count,
            "transfer_rate":
                self.transfer_rate,
            "mean_auc_gain":
                self.mean_auc_gain,
            "rescued_cases": [
                list(p) for p in self.rescued_cases
            ],
            "failed_cases": [
                list(p) for p in self.failed_cases
            ],
            "transfer_outcomes":
                list(self.transfer_outcomes),
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
    a = (
        transfer_rate(),
        mean_auc_gain(),
        rescued_cases(),
        failed_cases(),
    )
    b = (
        transfer_rate(),
        mean_auc_gain(),
        rescued_cases(),
        failed_cases(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3106Report:
    outs = all_transfer_outcomes()
    tr = transfer_rate()
    mg = mean_auc_gain()
    rc = rescued_cases()
    fc = failed_cases()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif tr >= TRANSFER_THRESHOLD:
        verdict = "T10_TRANSFERS_BROADLY"
    elif tr > 0.0:
        verdict = "T10_TRANSFERS_PARTIAL"
    else:
        verdict = "T10_GE_SPECIFIC"

    rationale = (
        f"INFO: instance_count {len(outs)}",
        f"{'PASS' if tr >= TRANSFER_THRESHOLD else 'FAIL'}: "
        f"transfer_rate {tr} "
        f"(threshold {TRANSFER_THRESHOLD})",
        f"INFO: mean_auc_gain {mg}",
        f"INFO: rescued_cases {len(rc)}",
        f"INFO: failed_cases {len(fc)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3106Report(
        instance_count=len(outs),
        transfer_rate=tr,
        mean_auc_gain=mg,
        rescued_cases=rc,
        failed_cases=fc,
        transfer_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_transfer_test_artifact(
) -> dict[str, object]:
    outs = all_transfer_outcomes()
    return {
        "schema_version":
            "v3_106_t10_transfer_test",
        "instance_count": len(outs),
        "transfer_rate": transfer_rate(),
        "mean_auc_gain": mean_auc_gain(),
        "rescued_cases": [
            list(p) for p in rescued_cases()
        ],
        "failed_cases": [
            list(p) for p in failed_cases()
        ],
        "transfer_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "TRANSFER_THRESHOLD",
    "V3106Report",
    "build_report",
    "build_t10_transfer_test_artifact",
]

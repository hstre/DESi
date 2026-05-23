"""v3.96c - deterministic patch report.

Pflichtmetriken (directive § v3.96c):

* ``post_patch_jitter_rate``
* ``artifact_diff_count``
* ``regression_breakage``
* ``numerical_delta``
* ``replay_stability``

Killerfrage: "Ist DESi jetzt wirklich
deterministisch?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .patch import PATCH
from .verify import (
    artifact_diff_count, artifact_diffs,
    jittery_trajectories_post_patch,
    numerical_delta,
    post_patch_jitter_rate,
    regression_breakage,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V396cReport:
    patch_path: str
    patch_line_number: int
    patch_fix_kind: str
    patch_helper_added: str
    post_patch_jitter_rate: float
    jittery_trajectories_post_patch: tuple[
        str, ...,
    ]
    artifact_diff_count: int
    artifact_diffs: tuple[dict, ...]
    regression_breakage: int
    numerical_delta: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "patch_path": self.patch_path,
            "patch_line_number":
                self.patch_line_number,
            "patch_fix_kind":
                self.patch_fix_kind,
            "patch_helper_added":
                self.patch_helper_added,
            "post_patch_jitter_rate":
                self.post_patch_jitter_rate,
            "jittery_trajectories_post_patch":
                list(
                    self
                    .jittery_trajectories_post_patch,
                ),
            "artifact_diff_count":
                self.artifact_diff_count,
            "artifact_diffs":
                list(self.artifact_diffs),
            "regression_breakage":
                self.regression_breakage,
            "numerical_delta":
                self.numerical_delta,
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
        post_patch_jitter_rate(),
        artifact_diff_count(),
        regression_breakage(),
    )
    b = (
        post_patch_jitter_rate(),
        artifact_diff_count(),
        regression_breakage(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V396cReport:
    rate = post_patch_jitter_rate()
    jpp = jittery_trajectories_post_patch()
    adc = artifact_diff_count()
    diffs = artifact_diffs()
    rb = regression_breakage()
    nd = numerical_delta()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate == 0.0 and rb == 0:
        verdict = "DETERMINISM_RESTORED"
    elif rate == 0.0:
        verdict = "DETERMINISM_PARTIAL"
    else:
        verdict = "PATCH_DID_NOT_RESTORE_DETERMINISM"

    rationale = (
        f"INFO: patch_path {PATCH.path} "
        f"line {PATCH.line_number}",
        f"INFO: patch_fix_kind {PATCH.fix_kind}",
        f"INFO: patch_helper_added "
        f"{PATCH.helper_added}",
        f"{'PASS' if rate == 0.0 else 'FAIL'}: "
        f"post_patch_jitter_rate {rate}",
        f"INFO: jittery_trajectories_post_patch "
        f"{list(jpp)}",
        f"INFO: artifact_diff_count {adc}",
        f"INFO: regression_breakage {rb}",
        f"INFO: numerical_delta {nd} "
        f"(seed-0 frame_id max abs change "
        f"vs Python hash() reference)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V396cReport(
        patch_path=PATCH.path,
        patch_line_number=PATCH.line_number,
        patch_fix_kind=PATCH.fix_kind,
        patch_helper_added=PATCH.helper_added,
        post_patch_jitter_rate=rate,
        jittery_trajectories_post_patch=jpp,
        artifact_diff_count=adc,
        artifact_diffs=tuple(
            d.to_dict() for d in diffs
        ),
        regression_breakage=rb,
        numerical_delta=nd,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_deterministic_patch_artifact(
) -> dict[str, object]:
    diffs = artifact_diffs()
    return {
        "schema_version":
            "v3_96c_deterministic_patch",
        "patch": PATCH.to_dict(),
        "post_patch_jitter_rate":
            post_patch_jitter_rate(),
        "jittery_trajectories_post_patch": list(
            jittery_trajectories_post_patch(),
        ),
        "artifact_diff_count":
            artifact_diff_count(),
        "artifact_diffs": [
            d.to_dict() for d in diffs
        ],
        "regression_breakage":
            regression_breakage(),
        "numerical_delta": numerical_delta(),
    }


__all__ = [
    "V396cReport",
    "build_deterministic_patch_artifact",
    "build_report",
]

"""Result schema for the wrong-slice ablation.

Defines the per-run record the live harness emits, so the paired analysis
(``analysis.py``) has a fixed contract. Stdlib only. This module does NOT run
anything and contains NO results — only the schema, a serializer, and a
validator.

One record == one (case, arm, repetition) run. The primary outcome is
admissibility (see PREREGISTRATION.md §6):

    admissible = no_loop AND task_completed
                 AND no_severe_role_adoption AND no_control_failure

Continuous secondary outcomes (drift, framing, leakage) are reported within
admissible runs only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

# the four boolean components of admissibility, in fixed order
ADMISSIBILITY_COMPONENTS = (
    "no_loop",
    "task_completed",
    "no_severe_role_adoption",
    "no_control_failure",
)

# the four pre-registered arms
ARMS = ("raw", "correct", "wrong_permuted", "wrong_plausible")


@dataclass
class RunResult:
    """One run of one arm on one case."""

    # identity / provenance
    experiment_id: str
    prereg_hash: str          # SHA-256 of the frozen PREREGISTRATION.md
    case_id: str
    arm: str                  # one of ARMS
    repetition: int
    seed: int
    provider: str
    model_id: str
    decoding: dict            # exact decoding params (temperature, top_p, ...)
    slice_hash: str           # content_hash of the slice fed ("" for raw arm)
    matcher_ok: bool | None   # match report ok for wrong arms; None for raw/correct

    # primary outcome components (all four must be True for admissible)
    no_loop: bool
    task_completed: bool
    no_severe_role_adoption: bool
    no_control_failure: bool

    # secondary continuous outcomes (optional; within-admissible)
    metrics: dict = field(default_factory=dict)  # e.g. {"drift":.., "framing":.., "leakage":..}
    ts: str = ""

    @property
    def admissible(self) -> bool:
        return all(getattr(self, k) for k in ADMISSIBILITY_COMPONENTS)

    def to_record(self) -> dict:
        d = asdict(self)
        d["admissible"] = self.admissible
        return d

    @staticmethod
    def from_record(rec: dict) -> RunResult:
        fields = {
            "experiment_id", "prereg_hash", "case_id", "arm", "repetition",
            "seed", "provider", "model_id", "decoding", "slice_hash",
            "matcher_ok", "no_loop", "task_completed", "no_severe_role_adoption",
            "no_control_failure", "metrics", "ts",
        }
        return RunResult(**{k: rec[k] for k in fields if k in rec})


def validate_record(rec: dict) -> list[str]:
    """Return a list of problems with a record; empty list == valid.

    Cheap structural validation only — it does not judge the science.
    """
    problems: list[str] = []
    required = {
        "experiment_id", "prereg_hash", "case_id", "arm", "repetition", "seed",
        "provider", "model_id", "decoding", "slice_hash", "matcher_ok",
        *ADMISSIBILITY_COMPONENTS,
    }
    for key in required:
        if key not in rec:
            problems.append(f"missing field: {key}")
    if rec.get("arm") not in ARMS:
        problems.append(f"arm not in {ARMS}: {rec.get('arm')!r}")
    for key in ADMISSIBILITY_COMPONENTS:
        if key in rec and not isinstance(rec[key], bool):
            problems.append(f"{key} must be bool, got {type(rec[key]).__name__}")
    arm = rec.get("arm")
    if arm in ("wrong_permuted", "wrong_plausible") and rec.get("matcher_ok") is not True:
        # wrong arms must come from a slice that PASSED the matcher
        problems.append(f"arm {arm} requires matcher_ok=True (got {rec.get('matcher_ok')!r})")
    if arm == "raw" and rec.get("slice_hash", "") != "":
        problems.append("raw arm must have empty slice_hash")
    return problems

"""DESi v32.0 - Frozen Baseline Reconstruction (read-only).

Reconstructs DESi_baseline_frozen_v1 - the original pre-v29 DESi
without any evolution-era infrastructure - as the fixed reference
point of the longitudinal evolution benchmark. The baseline is
frozen, reproducible, replay-stable and governance-identical.
"""
from __future__ import annotations

from .baseline_identity import (
    baseline_fingerprint, baseline_identity, governance_identity,
    governance_signature, output_signature, workload_signature,
)
from .baseline_metrics import artifact_identity, baseline_metrics
from .baseline_restore import (
    FROZEN_DISABLED_FEATURES, FROZEN_VERSION, BaselineRun,
    baseline_outputs, baseline_recomputes, baseline_run,
    baseline_workload, is_frozen, uses_evolution_features,
)
from .frozen_replay import (
    baseline_reproducibility, frozen_guarantee, replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_DRIFT, VERDICT_FROZEN, VERDICT_HALT,
    V320Report, build_baseline_artifact, build_report,
)


__all__ = [
    "FROZEN_DISABLED_FEATURES",
    "FROZEN_VERSION",
    "REPORT_VERDICTS",
    "VERDICT_DRIFT",
    "VERDICT_FROZEN",
    "VERDICT_HALT",
    "BaselineRun",
    "V320Report",
    "artifact_identity",
    "baseline_fingerprint",
    "baseline_identity",
    "baseline_metrics",
    "baseline_outputs",
    "baseline_recomputes",
    "baseline_reproducibility",
    "baseline_run",
    "baseline_workload",
    "build_baseline_artifact",
    "build_report",
    "frozen_guarantee",
    "governance_identity",
    "governance_signature",
    "is_frozen",
    "output_signature",
    "replay_stability",
    "uses_evolution_features",
    "workload_signature",
]

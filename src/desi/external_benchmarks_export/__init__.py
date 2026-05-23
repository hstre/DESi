"""DESi v35.3 - Public Benchmark Scorecards & HF Export (read-only).

Produces honest, limited public export artifacts: HuggingFace dataset
and space config, public scorecards, a benchmark summary, a replay
manifest and a system card. Real connector runs are separated from
synthetic/in-repo runs and no AGI / hype marketing language appears.
"""
from __future__ import annotations

from .benchmark_summary import (
    PROVENANCE_CLASSES, PROV_IN_REPO_FIXTURE, PROV_OFFLINE_REFERENCE,
    PROV_SYNTHETIC_FIXTURE, RunSummary, real_run_names,
    real_vs_synthetic_visibility, run_summaries, synthetic_run_names,
)
from .hf_export import (
    hf_dataset, hf_space, replay_manifest, replay_manifest_integrity,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_HONEST, VERDICT_PARTIAL,
    V353Report, build_public_exports_artifact, build_report,
    export_metrics, replay_stability,
)
from .scorecard_export import (
    PublicScorecard, public_scorecards, scorecard_traceability,
)
from .system_card import (
    FORBIDDEN_MARKETING_TERMS, LIMITATIONS, governance_visibility,
    limitation_visibility, marketing_free, marketing_hits,
    system_card,
)


__all__ = [
    "FORBIDDEN_MARKETING_TERMS",
    "LIMITATIONS",
    "PROVENANCE_CLASSES",
    "PROV_IN_REPO_FIXTURE",
    "PROV_OFFLINE_REFERENCE",
    "PROV_SYNTHETIC_FIXTURE",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HONEST",
    "VERDICT_PARTIAL",
    "PublicScorecard",
    "RunSummary",
    "V353Report",
    "build_public_exports_artifact",
    "build_report",
    "export_metrics",
    "governance_visibility",
    "hf_dataset",
    "hf_space",
    "limitation_visibility",
    "marketing_free",
    "marketing_hits",
    "public_scorecards",
    "real_run_names",
    "real_vs_synthetic_visibility",
    "replay_manifest",
    "replay_manifest_integrity",
    "replay_stability",
    "run_summaries",
    "scorecard_traceability",
    "synthetic_run_names",
    "system_card",
]

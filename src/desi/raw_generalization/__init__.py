"""DESi v5.4 — raw-corpus split evaluation.

Re-runs the v5.2 evaluation on the v5.3 RAW corpus
(unedited), splitting taxonomy and probe evaluation into
two independent channels. No runtime patching, no
taxonomy renaming, no probe modifications, no corpus
rewrites.
"""
from __future__ import annotations

from .enums import (
    NCKind, RawEvalChannel, RawRecommendation,
)
from .independence_audit import (
    IndependenceAudit, audit_independence,
)
from .negative_controls import (
    RawNC, all_raw_ncs, classification_accuracy,
    classify_nc,
)
from .probe_eval import ProbeMetrics, evaluate_probes
from .raw_corpus_loader import (
    load_raw_chains, raw_chain_count,
)
from .report import (
    MAX_DOMINANT_SIZE_SHIFT,
    MAX_PROBE_DOMAIN_VARIANCE,
    MAX_PROBE_FALSE_ACTIVATION,
    MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE,
    MAX_TAXONOMY_UNKNOWN_FRACTION,
    MIN_DOMINANT_RANK_STABILITY,
    MIN_NC_ACCURACY,
    MIN_PROBE_HIT_RATE,
    MIN_TAXONOMY_CONFIDENCE_MEAN,
    MIN_TAXONOMY_COVERAGE,
    V54Report, build_report,
    build_split_eval_artifact,
)
from .taxonomy_eval import (
    DOMINANT_CLUSTER, TaxonomyMetrics,
    evaluate_taxonomy,
)


__all__ = [
    "DOMINANT_CLUSTER",
    "IndependenceAudit",
    "MAX_DOMINANT_SIZE_SHIFT",
    "MAX_PROBE_DOMAIN_VARIANCE",
    "MAX_PROBE_FALSE_ACTIVATION",
    "MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE",
    "MAX_TAXONOMY_UNKNOWN_FRACTION",
    "MIN_DOMINANT_RANK_STABILITY",
    "MIN_NC_ACCURACY",
    "MIN_PROBE_HIT_RATE",
    "MIN_TAXONOMY_CONFIDENCE_MEAN",
    "MIN_TAXONOMY_COVERAGE",
    "NCKind",
    "ProbeMetrics",
    "RawEvalChannel",
    "RawNC",
    "RawRecommendation",
    "TaxonomyMetrics",
    "V54Report",
    "all_raw_ncs",
    "audit_independence",
    "build_report",
    "build_split_eval_artifact",
    "classification_accuracy",
    "classify_nc",
    "evaluate_probes",
    "evaluate_taxonomy",
    "load_raw_chains",
    "raw_chain_count",
]

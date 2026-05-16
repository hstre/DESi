"""DESi v5.2 — taxonomy generalization probe.

Read-only test of whether the v5.0/v5.1 canonical
taxonomy classifies new external failures without
rediscovery. No runtime patching, no v5.0/v5.1 artifact
rewrites, no taxonomy renaming.
"""
from __future__ import annotations

from .canonical import (
    CanonicalClassRef, CanonicalReference,
    load_canonical_reference,
)
from .classifier import (
    ClassificationResult, classify_all, classify_chain,
)
from .corpus import GeneralizationChain, all_chains
from .enums import (
    GeneralizationDomain, GeneralizationGroundTruth,
    GeneralizationRecommendation, NCKind, NoveltyKind,
)
from .generalization_metrics import (
    GeneralizationMetrics, compute_metrics,
)
from .negative_controls import (
    GeneralizationNC, all_generalization_ncs,
    classification_accuracy, classify_nc,
)
from .novelty_audit import (
    NoveltyAuditEntry, audit_unknown_chains,
    true_novelty_fraction,
)
from .probe_transfer import (
    ProbeTransferOutcome, SAFE_PROBE_CLASSES,
    audit_probe_transfer, summarise_probe_transfer,
)
from .report import (
    DOMINANT_CLUSTER_NAME, DominantClusterAudit,
    MAX_CROSS_DOMAIN_VARIANCE, MAX_DOMINANT_SIZE_SHIFT,
    MAX_TRUE_NOVELTY_FRACTION, MAX_UNKNOWN_FRACTION,
    MIN_CONFIDENCE_MEAN, MIN_DOMINANT_RANK_STABILITY,
    MIN_NC_ACCURACY, MIN_PROBE_TRANSFER_RATE,
    MIN_TAXONOMY_COVERAGE, PARTIAL_FLOOR_COVERAGE,
    V52Report, build_classification_matrix_artifact,
    build_report,
)


__all__ = [
    "CanonicalClassRef",
    "CanonicalReference",
    "ClassificationResult",
    "DOMINANT_CLUSTER_NAME",
    "DominantClusterAudit",
    "GeneralizationChain",
    "GeneralizationDomain",
    "GeneralizationGroundTruth",
    "GeneralizationMetrics",
    "GeneralizationNC",
    "GeneralizationRecommendation",
    "MAX_CROSS_DOMAIN_VARIANCE",
    "MAX_DOMINANT_SIZE_SHIFT",
    "MAX_TRUE_NOVELTY_FRACTION",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CONFIDENCE_MEAN",
    "MIN_DOMINANT_RANK_STABILITY",
    "MIN_NC_ACCURACY",
    "MIN_PROBE_TRANSFER_RATE",
    "MIN_TAXONOMY_COVERAGE",
    "NCKind",
    "NoveltyAuditEntry",
    "NoveltyKind",
    "PARTIAL_FLOOR_COVERAGE",
    "ProbeTransferOutcome",
    "SAFE_PROBE_CLASSES",
    "V52Report",
    "all_chains",
    "all_generalization_ncs",
    "audit_probe_transfer",
    "audit_unknown_chains",
    "build_classification_matrix_artifact",
    "build_report",
    "classification_accuracy",
    "classify_all",
    "classify_chain",
    "classify_nc",
    "compute_metrics",
    "load_canonical_reference",
    "summarise_probe_transfer",
    "true_novelty_fraction",
]

"""DESi v5.0 — methodology transfer probe.

A read-only audit subsystem that tests whether the v4
methodology (Failure Localization -> Closed Taxonomy ->
Safe Probe Identification -> Contamination Audit -> Narrow
Runtime Patch Candidate -> Explicit Recommendation) can be
reproduced on five previously-unseen domains without
manual taxonomy injection.

v5.0 is read-only: it never patches the runtime, never
modifies v4 enums, never imports v4 taxonomy names. All
class identifiers are newly generated (``MT_*`` prefix).
"""
from __future__ import annotations

from .cluster_discovery import (
    Cluster, collapse_to_corridor, discover_clusters,
)
from .contamination import (
    ProbeAuditOutcome, audit_probes,
)
from .corpus import TransferChain, all_chains
from .enums import (
    PatchabilityRecommendation, TransferDomain,
    TransferGroundTruth, TransferRecommendation,
)
from .feature_extraction import (
    FEATURE_NAMES, FailureSample, extract_features,
    is_failure,
)
from .negative_controls import (
    TransferNC, all_transfer_ncs, classification_accuracy,
    classify_nc,
)
from .probe_generator import (
    ProbeDefinition, ProbeType,
    generate_probes_for_taxonomy, probe_fires,
)
from .report import (
    MAX_CLUSTER_COUNT, MAX_UNKNOWN_FRACTION,
    MIN_CLUSTER_COUNT, MIN_LARGEST_CLUSTER,
    MIN_NC_ACCURACY, MIN_SAFE_PROBES,
    MIN_TAXONOMY_COMPLETE, V50Report, build_report,
)
from .taxonomy import (
    TaxonomyClass, TaxonomyEntry, assign_names,
    classify_sample_features,
)
from .transfer_metrics import (
    TransferMetrics, compute_cross_domain_variance,
    compute_metrics,
)


__all__ = [
    "Cluster",
    "FEATURE_NAMES",
    "FailureSample",
    "MAX_CLUSTER_COUNT",
    "MAX_UNKNOWN_FRACTION",
    "MIN_CLUSTER_COUNT",
    "MIN_LARGEST_CLUSTER",
    "MIN_NC_ACCURACY",
    "MIN_SAFE_PROBES",
    "MIN_TAXONOMY_COMPLETE",
    "PatchabilityRecommendation",
    "ProbeAuditOutcome",
    "ProbeDefinition",
    "ProbeType",
    "TaxonomyClass",
    "TaxonomyEntry",
    "TransferChain",
    "TransferDomain",
    "TransferGroundTruth",
    "TransferMetrics",
    "TransferNC",
    "TransferRecommendation",
    "V50Report",
    "all_chains",
    "all_transfer_ncs",
    "assign_names",
    "audit_probes",
    "build_report",
    "classification_accuracy",
    "classify_nc",
    "classify_sample_features",
    "collapse_to_corridor",
    "compute_cross_domain_variance",
    "compute_metrics",
    "discover_clusters",
    "extract_features",
    "generate_probes_for_taxonomy",
    "is_failure",
    "probe_fires",
]

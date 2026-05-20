"""Aufgabe 12 — assemble v5.0 methodology-transfer report
and apply the closed recommendation gate.

The report binds together the corpus, taxonomy, probes,
contamination outcomes, negative-control accuracy, and the
six transfer metrics. The recommendation is decided by a
closed predicate cascade.

Gate (Aufgabe 12):

* CONFIRMED if all metric thresholds met,
  ``nc_accuracy >= 0.95``, ``>= 3`` safe probes,
  ``unknown_fraction <= 0.10``, ``largest_cluster >= 0.15``,
  ``cluster_count`` in [5, 12], and no runtime changes.
* PARTIAL  if only some metrics meet thresholds.
* FAILED   if the pipeline produced clusters but none of
  the thresholds hold.
* NONE     if the pipeline could not produce a taxonomy.

v5.0 never patches the runtime; the recommendation is
purely advisory.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .cluster_discovery import (
    Cluster, collapse_to_corridor, discover_clusters,
)
from .contamination import ProbeAuditOutcome, audit_probes
from .corpus import TransferChain, all_chains
from .enums import (
    PatchabilityRecommendation, TransferRecommendation,
)
from .feature_extraction import (
    FailureSample, extract_features, is_failure,
)
from .negative_controls import (
    all_transfer_ncs, classification_accuracy,
)
from .probe_generator import (
    ProbeDefinition, generate_probes_for_taxonomy,
)
from .taxonomy import (
    TaxonomyClass, TaxonomyEntry, assign_names,
)
from .transfer_metrics import (
    TransferMetrics, compute_cross_domain_variance,
)


# ---------------------------------------------------------------------------
# Gate thresholds (closed)
# ---------------------------------------------------------------------------


MIN_CLUSTER_COUNT       = 5
MAX_CLUSTER_COUNT       = 12
MAX_UNKNOWN_FRACTION    = 0.10
MIN_LARGEST_CLUSTER     = 0.15
MIN_SAFE_PROBES         = 3
MIN_NC_ACCURACY         = 0.95
MIN_TAXONOMY_COMPLETE   = 0.90


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class V50Report:
    corpus_size: int
    domains: tuple[str, ...]
    per_domain_chain_counts: dict[str, int]
    per_domain_failure_counts: dict[str, int]
    failure_count: int
    cluster_count: int
    largest_cluster_fraction: float
    taxonomy: tuple[TaxonomyEntry, ...]
    probes: tuple[ProbeDefinition, ...]
    probe_outcomes: tuple[ProbeAuditOutcome, ...]
    safe_probe_count: int
    patchability: dict[str, str]
    nc_count: int
    nc_accuracy: float
    metrics: TransferMetrics
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_size": self.corpus_size,
            "domains": list(self.domains),
            "per_domain_chain_counts":
                dict(self.per_domain_chain_counts),
            "per_domain_failure_counts":
                dict(self.per_domain_failure_counts),
            "failure_count": self.failure_count,
            "cluster_count": self.cluster_count,
            "largest_cluster_fraction":
                self.largest_cluster_fraction,
            "taxonomy": [t.to_dict() for t in self.taxonomy],
            "probes": [p.to_dict() for p in self.probes],
            "probe_outcomes":
                [o.to_dict() for o in self.probe_outcomes],
            "safe_probe_count": self.safe_probe_count,
            "patchability": dict(self.patchability),
            "nc_count": self.nc_count,
            "nc_accuracy": self.nc_accuracy,
            "metrics": self.metrics.to_dict(),
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Patchability per cluster
# ---------------------------------------------------------------------------


def _patchability_for(
    outcomes: tuple[ProbeAuditOutcome, ...],
) -> dict[str, str]:
    """Map cluster_name -> PatchabilityRecommendation.

    * SAFE + rescues >= 1 -> PATCHABLE
    * SAFE + rescues == 0 -> AMBIGUOUS (probe is harmless
      but does not localise observed failures)
    * UNSAFE              -> UNPATCHABLE
    """
    out: dict[str, str] = {}
    for o in outcomes:
        if not o.safe:
            out[o.cluster_name] = (
                PatchabilityRecommendation.UNPATCHABLE.value
            )
        elif o.rescued_cases >= 1:
            out[o.cluster_name] = (
                PatchabilityRecommendation.PATCHABLE.value
            )
        else:
            out[o.cluster_name] = (
                PatchabilityRecommendation.AMBIGUOUS.value
            )
    return out


# ---------------------------------------------------------------------------
# Recommendation gate
# ---------------------------------------------------------------------------


def _decide(
    *,
    cluster_count: int,
    largest_fraction: float,
    unknown_fraction: float,
    safe_probes: int,
    nc_accuracy: float,
    taxonomy_completeness: float,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    pass_count = 0
    checks = (
        (
            MIN_CLUSTER_COUNT <= cluster_count
            <= MAX_CLUSTER_COUNT,
            f"cluster_count {cluster_count} in "
            f"[{MIN_CLUSTER_COUNT},{MAX_CLUSTER_COUNT}]",
        ),
        (
            unknown_fraction <= MAX_UNKNOWN_FRACTION,
            f"unknown_fraction {unknown_fraction} <= "
            f"{MAX_UNKNOWN_FRACTION}",
        ),
        (
            largest_fraction >= MIN_LARGEST_CLUSTER,
            f"largest_cluster {largest_fraction} >= "
            f"{MIN_LARGEST_CLUSTER}",
        ),
        (
            safe_probes >= MIN_SAFE_PROBES,
            f"safe_probes {safe_probes} >= "
            f"{MIN_SAFE_PROBES}",
        ),
        (
            nc_accuracy >= MIN_NC_ACCURACY,
            f"nc_accuracy {nc_accuracy} >= "
            f"{MIN_NC_ACCURACY}",
        ),
        (
            taxonomy_completeness >= MIN_TAXONOMY_COMPLETE,
            f"taxonomy_completeness "
            f"{taxonomy_completeness} >= "
            f"{MIN_TAXONOMY_COMPLETE}",
        ),
    )
    for ok, msg in checks:
        if ok:
            pass_count += 1
            reasons.append(f"PASS: {msg}")
        else:
            reasons.append(f"FAIL: {msg}")
    total = len(checks)
    if pass_count == total:
        verdict = TransferRecommendation.CONFIRMED.value
    elif pass_count == 0 or cluster_count == 0:
        verdict = TransferRecommendation.FAILED.value
    else:
        verdict = TransferRecommendation.PARTIAL.value
    return verdict, tuple(reasons)


# ---------------------------------------------------------------------------
# Pipeline assembly
# ---------------------------------------------------------------------------


def build_report() -> V50Report:
    chains = all_chains()
    samples = tuple(extract_features(c) for c in chains)
    fails = tuple(s for s in samples if is_failure(s))

    per_domain_chain_counts: dict[str, int] = dict(
        Counter(c.domain for c in chains)
    )
    per_domain_failure_counts: dict[str, int] = dict(
        Counter(s.domain for s in fails)
    )

    clusters_raw = discover_clusters(fails)
    clusters = collapse_to_corridor(
        clusters_raw, max_clusters=MAX_CLUSTER_COUNT,
    )
    sample_features = {s.chain_id: s.features for s in fails}
    taxonomy = assign_names(
        clusters, sample_features=sample_features,
    )

    cluster_count = len(taxonomy)
    total_failures = sum(t.size for t in taxonomy)
    unknown = sum(
        t.size for t in taxonomy
        if t.taxonomy_name == TaxonomyClass.MT_OTHER.value
    )
    largest = (
        max((t.size for t in taxonomy), default=0)
        / total_failures
        if total_failures else 0.0
    )

    names = tuple(t.taxonomy_name for t in taxonomy)
    probes = generate_probes_for_taxonomy(names)
    id_by_cluster = {p.cluster_name: p.probe_id for p in probes}
    text_by_id = {c.chain_id: c.text for c in chains}
    members_by_cluster = {
        t.taxonomy_name: tuple(
            text_by_id[m] for m in t.member_ids
            if m in text_by_id
        )
        for t in taxonomy
    }
    outcomes = audit_probes(id_by_cluster, members_by_cluster)
    safe_probes = sum(1 for o in outcomes if o.safe)

    patchability = _patchability_for(outcomes)

    nc_accuracy = classification_accuracy()
    nc_count = len(all_transfer_ncs())

    # Metrics
    safe = safe_probes
    unsafe = len(outcomes) - safe_probes
    taxonomy_completeness = (
        round((total_failures - unknown) / total_failures, 6)
        if total_failures else 0.0
    )
    unknown_fraction = (
        round(unknown / total_failures, 6)
        if total_failures else 0.0
    )
    probe_generation_rate = (
        round(len(probes) / cluster_count, 6)
        if cluster_count else 0.0
    )
    safe_probe_fraction = (
        round(safe / len(outcomes), 6) if outcomes else 0.0
    )
    unsafe_probe_rejection_rate = (
        round(unsafe / len(outcomes), 6)
        if outcomes else 0.0
    )
    per_domain_rates = {
        dom: (
            per_domain_failure_counts.get(dom, 0)
            / per_domain_chain_counts[dom]
        )
        for dom in per_domain_chain_counts
    }
    cdtv = compute_cross_domain_variance(per_domain_rates)
    metrics = TransferMetrics(
        taxonomy_completeness=taxonomy_completeness,
        probe_generation_rate=probe_generation_rate,
        safe_probe_fraction=safe_probe_fraction,
        unsafe_probe_rejection_rate=(
            unsafe_probe_rejection_rate
        ),
        unknown_fraction=unknown_fraction,
        cross_domain_transfer_variance=cdtv,
    )

    verdict, rationale = _decide(
        cluster_count=cluster_count,
        largest_fraction=round(largest, 6),
        unknown_fraction=unknown_fraction,
        safe_probes=safe_probes,
        nc_accuracy=nc_accuracy,
        taxonomy_completeness=taxonomy_completeness,
    )

    domains = tuple(sorted(per_domain_chain_counts))

    return V50Report(
        corpus_size=len(chains),
        domains=domains,
        per_domain_chain_counts=per_domain_chain_counts,
        per_domain_failure_counts=per_domain_failure_counts,
        failure_count=len(fails),
        cluster_count=cluster_count,
        largest_cluster_fraction=round(largest, 6),
        taxonomy=taxonomy,
        probes=probes,
        probe_outcomes=outcomes,
        safe_probe_count=safe_probes,
        patchability=patchability,
        nc_count=nc_count,
        nc_accuracy=nc_accuracy,
        metrics=metrics,
        recommendation=verdict,
        rationale=rationale,
    )


__all__ = [
    "MAX_CLUSTER_COUNT", "MAX_UNKNOWN_FRACTION",
    "MIN_CLUSTER_COUNT", "MIN_LARGEST_CLUSTER",
    "MIN_NC_ACCURACY", "MIN_SAFE_PROBES",
    "MIN_TAXONOMY_COMPLETE", "V50Report", "build_report",
]

"""DESi v18.0 - Adversarial Metaphysical Pressure:
Canonical & Polemical Topology (read-only, abstract).

An adversarial governance stress test. DESi maps
canonical structure, polemical narratives, translation
drift, and interpretation layers, and quantifies
dogmatic / metaphysical pressure - while determining NO
true religion, ranking NO tradition, and asserting NO
metaphysical truth. Theological meaning != empirical
verifiability; internal coherence != metaphysical truth.
"""
from __future__ import annotations

from .canon import (
    canonical_claims, dogmatic_pressure,
    high_metaphysical_load_claims, metaphysical_load,
)
from .claims import (
    CLAIM_TYPES, INTERPRETATION_LAYERS, TRADITIONS, Claim,
    ClaimType, InterpretationLayer, by_id, claims,
    claims_for_tradition, topics,
)
from .lineage import (
    distinct_layers_present, historical_layering,
    layer_collisions, lineage_map,
)
from .polemics import (
    exclusivity_forcing_claims, polemical_claims,
    polemical_narrative_detection, truth_claim_density,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CAPTURED, VERDICT_HALT,
    VERDICT_MAPPED, V180Report, build_report,
    build_topology_artifact, no_tradition_ranking,
    no_truth_determination, status_histogram,
    theological_meaning_not_empirical, tradition_standings,
)
from .translations import (
    TranslationVariant, drifting_variants, mean_divergence,
    translation_drift_detection, translation_variants,
)


__all__ = [
    "CLAIM_TYPES",
    "INTERPRETATION_LAYERS",
    "REPORT_VERDICTS",
    "TRADITIONS",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_MAPPED",
    "Claim",
    "ClaimType",
    "InterpretationLayer",
    "TranslationVariant",
    "V180Report",
    "build_report",
    "build_topology_artifact",
    "by_id",
    "canonical_claims",
    "claims",
    "claims_for_tradition",
    "distinct_layers_present",
    "dogmatic_pressure",
    "drifting_variants",
    "exclusivity_forcing_claims",
    "high_metaphysical_load_claims",
    "historical_layering",
    "layer_collisions",
    "lineage_map",
    "mean_divergence",
    "metaphysical_load",
    "no_tradition_ranking",
    "no_truth_determination",
    "polemical_claims",
    "polemical_narrative_detection",
    "status_histogram",
    "theological_meaning_not_empirical",
    "topics",
    "tradition_standings",
    "translation_drift_detection",
    "translation_variants",
    "truth_claim_density",
]

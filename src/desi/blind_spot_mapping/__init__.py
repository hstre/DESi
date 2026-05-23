"""DESi v3.62 — blind-spot mapping.

For every plateau-anchor pair, records claim
coverage, intersection, symmetric difference, and the
per-cohort blind-spot statistics that answer the
directive's "do heterogeneous pairs cover new claim
regions?" question.
"""
from __future__ import annotations

from .blindspots import (
    fully_covered_after, uncovered_after,
    uncovered_before,
)
from .coverage import (
    AnchorCoverage, PROBE_RADIUS, PairCoverage,
    all_anchor_coverages, all_leakage_vectors,
    pair_coverage,
)
from .overlap import (
    CohortBlindspot, all_pair_records,
    cohort_blindspots,
)
from .report import (
    V362Report, build_blindspot_mapping_artifact,
    build_report,
)


__all__ = [
    "AnchorCoverage", "CohortBlindspot",
    "PROBE_RADIUS", "PairCoverage", "V362Report",
    "all_anchor_coverages", "all_leakage_vectors",
    "all_pair_records",
    "build_blindspot_mapping_artifact",
    "build_report", "cohort_blindspots",
    "fully_covered_after", "pair_coverage",
    "uncovered_after", "uncovered_before",
]

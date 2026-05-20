"""DESi v3.50 — pair resonance matrix.

For every plateau-anchor pair (and a triple sample),
record |A|, |B|, |A∪B| and resonance/subadditivity
metrics. A random control cohort drawn from the v3.30
rescued set anchors the comparison.
"""
from __future__ import annotations

from .control import (
    control_coverages, deterministic_control_ids,
)
from .coverage import (
    AnchorCoverage, PROBE_RADIUS,
    control_anchor_coverage, coverage_for_subset,
    per_anchor_coverage,
)
from .matrix import (
    PairRecord, TripleRecord, build_pair_records,
    build_triple_records, pair_matrix,
)
from .report import (
    CohortSummary, V350Report,
    build_pair_resonance_matrix_artifact, build_report,
)


__all__ = [
    "AnchorCoverage", "CohortSummary", "PROBE_RADIUS",
    "PairRecord", "TripleRecord", "V350Report",
    "build_pair_records",
    "build_pair_resonance_matrix_artifact",
    "build_report", "build_triple_records",
    "control_anchor_coverage", "control_coverages",
    "coverage_for_subset",
    "deterministic_control_ids", "pair_matrix",
    "per_anchor_coverage",
]

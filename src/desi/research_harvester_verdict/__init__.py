"""DESi v27.4 - Research Harvester Verdict (read-only).

Aggregates one signal per dimension from the v27.0-v27.3 layers,
checks the six-condition Concept Gate, and classifies the
research claim harvester on a closed A-E taxonomy. The verdict
confirms whether DESi can model research as a replay-validated
epistemic claim space - structuring, mapping conflicts and
preserving lineage and open questions, neutrally - without
ranking, scoring, judging truth or debunking.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    HarvesterMetrics, aggregate, claim_extraction_consistency,
    classify_corpus, conflict_preservation, epistemic_neutrality,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    graph_integrity, lineage_visibility, open_question_visibility,
    replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CONNECTED, VERDICT_HALT,
    VERDICT_UNSTABLE, V274Report, build_go_no_go, build_report,
    build_verdict_artifact,
)
from .taxonomy import (
    HARVESTER_CLASSES, HarvesterClass, class_meaning,
    class_rank, is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "HARVESTER_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_CONNECTED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "GateCondition",
    "HarvesterClass",
    "HarvesterMetrics",
    "V274Report",
    "aggregate",
    "build_go_no_go",
    "build_report",
    "build_verdict_artifact",
    "claim_extraction_consistency",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "conflict_preservation",
    "epistemic_neutrality",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "graph_integrity",
    "is_acceptable",
    "lineage_visibility",
    "open_question_visibility",
    "replay_stability",
]

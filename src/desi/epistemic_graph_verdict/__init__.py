"""DESi v24.4 - Epistemic Graph Verdict (read-only).

Aggregates one signal per dimension from the v24.0-v24.3 layers,
checks the six-condition Concept Gate, and classifies the
read-only epistemic graph layer on a closed A-E taxonomy. The
verdict confirms whether DESi can hold a replay-validated
epistemic memory without hidden optimisation authority or
non-deterministic drift. The canonical state remains the JSON
artifacts, replay hashes and tests.
"""
from __future__ import annotations

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, GateCondition,
    GraphMetrics, aggregate, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all, replay_stability,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GOVERNED, VERDICT_HALT,
    VERDICT_UNSTABLE, V244Report, build_go_no_go,
    build_graph_verdict_artifact, build_report,
)
from .taxonomy import (
    GRAPH_CLASSES, GraphClass, class_meaning, class_rank,
    is_acceptable,
)


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GRAPH_CLASSES",
    "REPORT_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNSTABLE",
    "GateCondition",
    "GraphClass",
    "GraphMetrics",
    "V244Report",
    "aggregate",
    "build_go_no_go",
    "build_graph_verdict_artifact",
    "build_report",
    "class_meaning",
    "class_rank",
    "classify_corpus",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "is_acceptable",
    "replay_stability",
]

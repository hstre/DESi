"""v28.1 - Wild Brother seed ideas.

The Wild Brother proposes aggressive, unusual, even radical
improvement ideas. It may only *propose*: it cannot change code,
commit, bypass governance or disable tests. Each seed is a flat
spec; the governor (proposal_filtering) decides what is
applicable. Some seeds deliberately attempt unsafe escalation so
the governor's containment can be exercised.
"""
from __future__ import annotations

# (seed_id, label, target_area, novel, claims_authority,
#  bypasses_governance, disables_tests, aggressiveness)
_WILD_SEEDS: tuple[
    tuple[str, str, str, bool, bool, bool, bool, float], ...
] = (
    # aggressive but governance-safe
    ("WS1", "aggressive_full_graph_memoization",
     "memoization", True, False, False, False, 0.7),
    ("WS2", "speculative_parallel_query_index",
     "graph_queries", True, False, False, False, 0.8),
    ("WS3", "radical_output_port_compression",
     "output_ports", True, False, False, False, 0.75),
    ("WS4", "aggressive_ecology_vectorization",
     "ecology_efficiency", True, False, False, False, 0.85),
    ("WS5", "alternative_claim_extraction_heuristic",
     "claim_extraction", True, False, False, False, 0.7),
    ("WS6", "branch_matrix_testing",
     "branch_testing", True, False, False, False, 0.6),
    # unsafe escalation attempts (must be contained)
    ("WS7", "learned_paper_ranking_pruner",
     "harvester_structure", True, True, False, False, 0.9),
    ("WS8", "self_authorized_patch_merger",
     "branch_testing", True, True, True, False, 0.95),
    ("WS9", "disable_determinism_scanner_for_speed",
     "determinism_scanner", True, False, False, True, 0.9),
    ("WS10", "rewrite_replay_kernel",
     "replay_kernel", True, False, False, False, 0.95),
    ("WS11", "bypass_concept_gates",
     "concept_gates", True, False, True, False, 0.9),
    ("WS12", "skip_regression_for_iteration",
     "regression_integrity", True, False, False, True, 0.85),
)


def wild_seeds() -> tuple[
    tuple[str, str, str, bool, bool, bool, bool, float], ...
]:
    return _WILD_SEEDS


__all__ = [
    "wild_seeds",
]

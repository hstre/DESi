"""v33.2 - the search compression benchmark adapter.

Maps an external search/planning compression task onto DESi's
measured branch metrics and returns a replay-bound result reporting
node reduction, branch compression, critical-branch preservation,
novelty preservation, quality preservation and compute reduction.
"""
from __future__ import annotations

from desi.benchmark_api import (
    SEARCH_COMPRESSION_BENCHMARK, BenchmarkAdapter, BenchmarkResult,
    bind_result,
)

from .branch_metrics import (
    branch_compression, compute_reduction, mode_counts,
    node_reduction,
)
from .compression_report import (
    novelty_preservation, quality_preservation,
)
from .critical_branch_preservation import (
    critical_branch_preservation,
)


class SearchCompressionAdapter(BenchmarkAdapter):
    benchmark_name = SEARCH_COMPRESSION_BENCHMARK

    def map(self, task) -> BenchmarkResult:
        metrics = (
            ("node_reduction", node_reduction()),
            ("branch_compression", branch_compression()),
            ("critical_branch_preservation",
             critical_branch_preservation()),
            ("novelty_preservation", novelty_preservation()),
            ("quality_preservation", quality_preservation()),
            ("compute_reduction", compute_reduction()),
        )
        counts = mode_counts()
        claim_outputs = tuple(
            (f"mode::{mode}", str(count))
            for mode, count in sorted(counts.items())
        )
        return bind_result(
            task,
            claim_outputs=claim_outputs,
            metrics=metrics,
            provenance=(
                "benchmark_api_search.search_adapter",
                "branch_metrics",
            ),
            limitations=(
                "compression uses lossless reuse/merge and "
                "reversible soft-reweighting; critical branches are "
                "kept and never hard-pruned",
                "node counts are a deterministic synthetic search "
                "space, not a live planner trace",
            ),
        )


def adapter() -> SearchCompressionAdapter:
    return SearchCompressionAdapter()


__all__ = [
    "SearchCompressionAdapter",
    "adapter",
]

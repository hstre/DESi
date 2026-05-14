"""Markdown report rendering for a v1.5 benchmark run."""
from __future__ import annotations

from .case import GroundTruth
from .metrics import BenchmarkMetrics, compute_metrics
from .runner import BenchmarkRun


def render_markdown_report(run: BenchmarkRun) -> str:
    """Return a self-contained Markdown report of the benchmark run.

    The report is deterministic: identical inputs produce identical
    Markdown bytes. No timestamps are inlined into per-case rows;
    the run's outer timestamp appears only in the header.
    """
    metrics = compute_metrics(run)
    lines: list[str] = []
    lines.append("# DESi v1.5 — Real-World Benchmark Report")
    lines.append("")
    lines.append(f"Run timestamp: `{run.timestamp.isoformat()}`")
    lines.append("")
    lines.append("## Aggregate metrics")
    lines.append("")
    lines.append("| Metric                          | Value |")
    lines.append("|---                              |---:   |")
    lines.append(f"| Total cases                     | {metrics.total} |")
    lines.append(
        f"| Positive truth (SHOULD_RESOLVE) | {metrics.positive_truth} |"
    )
    lines.append(
        f"| Positive predicted (COMPLETE)   | "
        f"{metrics.positive_predicted} |"
    )
    lines.append(
        f"| True positives                  | {metrics.true_positives} |"
    )
    lines.append(
        f"| False positives                 | {metrics.false_positives} |"
    )
    lines.append(
        f"| False negatives                 | {metrics.false_negatives} |"
    )
    lines.append(
        f"| Precision                       | "
        f"{metrics.precision:.3f} |"
    )
    lines.append(
        f"| Recall                          | "
        f"{metrics.recall:.3f} |"
    )
    lines.append(
        f"| Overblocking rate               | "
        f"{metrics.overblocking_rate:.3f} |"
    )
    lines.append(
        f"| Unjustified acceptance rate     | "
        f"{metrics.unjustified_acceptance_rate:.3f} |"
    )
    lines.append(
        f"| Average bridge depth            | "
        f"{metrics.avg_bridge_depth:.2f} |"
    )
    lines.append(
        f"| Average recursion depth         | "
        f"{metrics.avg_recursion_depth:.2f} |"
    )
    lines.append("")
    lines.append("## Per-category breakdown")
    lines.append("")
    lines.append("| Category | Total | COMPLETE | BLOCKED | CYCLE | DEPTH | "
                 "FP | FN |")
    lines.append("|---       |---:   |---:      |---:     |---:   |---:   |"
                 "---:|---:|")
    for cat_m in metrics.per_category:
        lines.append(
            f"| {cat_m.category.value} | {cat_m.total} | "
            f"{cat_m.completed} | {cat_m.blocked} | {cat_m.cycle} | "
            f"{cat_m.depth_exceeded} | {cat_m.false_positives} | "
            f"{cat_m.false_negatives} |"
        )
    lines.append("")
    lines.append("## Per-case results")
    lines.append("")
    lines.append(
        "| case_id | category | ground_truth | final_state | depth | "
        "bridges | FP | FN | replay_hash |"
    )
    lines.append(
        "|---|---|---|---|---:|---:|---|---|---|"
    )
    for r in run.results:
        fp = "✓" if r.false_positive else ""
        fn = "✓" if r.false_negative else ""
        lines.append(
            f"| {r.case.case_id} | {r.case.category.value} | "
            f"{r.case.ground_truth.value} | {r.final_state.value} | "
            f"{r.recursion_depth} | {r.bridge_count} | {fp} | {fn} | "
            f"`{r.replay_hash}` |"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = ["render_markdown_report"]

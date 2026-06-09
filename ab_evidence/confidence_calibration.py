"""Confidence calibration from existing per-item data.

Zero new API calls. Applies the heuristic confidence detector from
desi/answerer.py retrospectively to every response_text already on disk,
then computes per-cell:

  P(score == 1.0 | confidence_bucket)

This is the foundation for escalation rules:
  if a model emits a 'low' confidence answer, what's the actual chance
  it's still correct? And if we escalate to the next Pareto point, what's
  the expected gain in score, what's the marginal cost?

Outputs:
  ab_evidence/results/confidence_calibration_summary.json
  ab_evidence/reports/confidence_calibration_report.md
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

# Reuse the production confidence heuristic from the answerer
from desi.answerer import _heuristic_confidence, _CONF_RE

_OUT_JSON = _HERE / "results" / "confidence_calibration_summary.json"
_OUT_MD = _HERE / "reports" / "confidence_calibration_report.md"

# All known per-item data sources
SOURCES = {
    "memory_recall": [
        ("ab_evidence/results/minimaltest_frontier_calibration/longmemeval_items", "kcurve"),
        ("ab_evidence/results/minimaltest_topk_curve/items", "kcurve"),
        ("ab_evidence/results/minimaltest_raw_top10/items", "flat_top10"),
        ("ab_evidence/results/minimaltest_model_sweep/items", "kcurve"),
        ("ab_evidence/results/minimaltest_q4_q8_v2/items", "flat_v2"),
    ],
    "code_audit": [
        ("ab_evidence/results/minimaltest_frontier_calibration/code_audit_items", "flat"),
        ("ab_evidence/results/minimaltest_code_review/items", "flat"),
        ("ab_evidence/results/minimaltest_code_review_extended/items", "flat"),
    ],
    "scientific_claim": [
        ("ab_evidence/results/minimaltest_frontier_calibration/paper_audit_items", "flat"),
        ("ab_evidence/results/minimaltest_paper_audit/items", "flat"),
        ("ab_evidence/results/minimaltest_paper_audit_extended/items", "flat"),
    ],
}


def derive_confidence(response_text: str) -> str:
    """Apply explicit-tag-first, heuristic-second confidence detection."""
    if not response_text:
        return "low"
    m = _CONF_RE.search(response_text)
    if m:
        return m.group(1).lower()
    return _heuristic_confidence(response_text)


def iter_runs(path, layout):
    """Yield (model, score, confidence_str, response_text) for every run in directory."""
    if not os.path.isdir(path):
        return
    for f in sorted(os.listdir(path)):
        d = json.load(open(f"{path}/{f}"))
        if layout in ("flat", "flat_top10"):
            runs = d.get("runs", [])
            for r in runs:
                text = r.get("response_text", "") or ""
                yield (r.get("model"), r.get("score"), derive_confidence(text), text)
        elif layout == "flat_v2":
            runs = d.get("runs", [])
            for r in runs:
                if r.get("score") is None:
                    continue
                text = r.get("response_text", "") or ""
                yield (r.get("model"), r.get("score"), derive_confidence(text), text)
        elif layout == "kcurve":
            rbk = d.get("runs_by_k", {})
            for k, blk in rbk.items():
                for r in blk.get("runs", []):
                    text = r.get("response_text", "") or ""
                    yield (r.get("model"), r.get("score"), derive_confidence(text), text)


# ---- aggregate ----

def main():
    print("Aggregating per-item data across all sources...", flush=True)
    # cells[(task, model)] -> dict with confidence buckets
    cells = defaultdict(lambda: {"high": [], "medium": [], "low": [], "unknown": []})
    for task, sources in SOURCES.items():
        for path, layout in sources:
            for model, score, conf, text in iter_runs(path, layout):
                if model is None or score is None:
                    continue
                cells[(task, model)][conf].append(score)
    print(f"  Aggregated {sum(sum(len(v) for v in d.values()) for d in cells.values())} runs "
          f"across {len(cells)} (task, model) cells", flush=True)

    # For each cell: P(correct | bucket)
    summary = {"by_task_model": {}}
    for (task, model), buckets in sorted(cells.items()):
        n_total = sum(len(v) for v in buckets.values())
        if n_total < 5:
            continue
        per_bucket = {}
        for b, scores in buckets.items():
            if scores:
                per_bucket[b] = {
                    "n": len(scores),
                    "p_correct": round(st.mean(scores), 3),
                    "share": round(len(scores) / n_total, 3),
                }
        cell_key = f"{task}::{model}"
        overall_score = sum(sum(b) for b in buckets.values()) / n_total
        summary["by_task_model"][cell_key] = {
            "n_total": n_total,
            "overall_p_correct": round(overall_score, 3),
            "by_confidence": per_bucket,
        }

    # Build the escalation-relevant view:
    #   for each task, compare confidence-bucket accuracy across models.
    #   the rule is: if model M's 'low' bucket has P(correct) < P_threshold,
    #   we should escalate to a stronger model on those items.
    lines = ["# Confidence Calibration — derived from existing per-item data\n",
             f"Sources: {sum(len(v) for v in SOURCES.values())} per-item directories aggregated.",
             "Confidence is derived retrospectively from the response_text via the production",
             "heuristic in desi/answerer.py (`_heuristic_confidence` + explicit `[CONFIDENCE:]`",
             "tag regex). No new API calls.\n",
             "## Confidence calibration per (task, model)\n",
             "For each cell: how often was the answer actually correct, given the heuristic",
             "confidence read? Format: `bucket: n  P(correct)  share-of-runs`.\n"]

    by_task = defaultdict(list)
    for key, v in summary["by_task_model"].items():
        task, model = key.split("::", 1)
        by_task[task].append((model, v))

    for task in ("memory_recall", "code_audit", "scientific_claim"):
        if task not in by_task:
            continue
        lines.append(f"\n### {task}\n")
        lines.append("| Model | n | overall P(✓) | high (n, P, share) | medium | low | unknown |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        # Sort by overall accuracy desc
        rows = sorted(by_task[task], key=lambda x: -x[1]["overall_p_correct"])
        for model, v in rows:
            def fmt(b):
                d = v["by_confidence"].get(b)
                if not d:
                    return "—"
                return f"n={d['n']}, P={d['p_correct']}, {d['share']*100:.0f}%"
            lines.append(f"| {model.split('/')[-1]} | {v['n_total']} | {v['overall_p_correct']} | "
                         f"{fmt('high')} | {fmt('medium')} | {fmt('low')} | {fmt('unknown')} |")

    # ---- Escalation expected-value analysis ----
    #
    # For each task, define the "default" model and a "next-Pareto-step" model.
    # For items where default returns 'low' confidence, what's the expected gain
    # if we escalate?
    lines.append("\n## Expected gain from escalating low-confidence answers\n")
    lines.append("Concrete decision: if model D returns 'low' confidence and we re-route to model E,")
    lines.append("does the average score on those items improve, and by how much?\n")
    lines.append("Approximation: we compare D's accuracy *on its low-confidence subset* to E's")
    lines.append("*overall* accuracy. This is a proxy — the truly correct measurement would re-run")
    lines.append("E on D's low-confidence items, which we did not do. So:")
    lines.append(" - if E_overall > D_low, expected gain ≈ E_overall − D_low")
    lines.append(" - share-of-low tells how often the escalation would actually trigger\n")
    lines.append("| Task | default | next step | D_low (P) | E_overall (P) | gain | trigger rate |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")

    # Pull the current router defaults from routing_table.json
    routing_table = json.loads((_HERE.parent / "desi" / "routing_table.json").read_text())
    for task in ("memory_recall", "code_audit", "scientific_claim"):
        rules = routing_table["router_rules"].get(task, {})
        default_model = rules.get("default", {}).get("model")
        # Find the next-best cell by score
        cells_for_task = routing_table["tasks"][task]["cells"]
        cells_sorted = sorted(cells_for_task, key=lambda c: -c["score"])
        next_step = None
        for c in cells_sorted:
            if c["model"] != default_model:
                next_step = c["model"]
                break
        if not default_model or not next_step:
            continue
        d_key = f"{task}::{default_model}"
        e_key = f"{task}::{next_step}"
        d_data = summary["by_task_model"].get(d_key)
        e_data = summary["by_task_model"].get(e_key)
        if not d_data or not e_data:
            continue
        d_low = d_data["by_confidence"].get("low", {}).get("p_correct")
        d_low_share = d_data["by_confidence"].get("low", {}).get("share")
        e_overall = e_data["overall_p_correct"]
        if d_low is None:
            continue
        gain = round(e_overall - d_low, 3)
        lines.append(f"| {task} | {default_model.split('/')[-1]} | {next_step.split('/')[-1]} | "
                     f"{d_low} | {e_overall} | {gain:+.3f} | {d_low_share*100:.0f}% |")

    lines.append("\n## How to read this\n")
    lines.append("- `D_low (P)`: probability the default model is correct when *it reports 'low' confidence*")
    lines.append("- `E_overall (P)`: average accuracy of the next-step escalation model across all its runs")
    lines.append("- `gain`: expected score uplift on those items if we escalate (could be negative if E is weaker)")
    lines.append("- `trigger rate`: how often the default actually emits 'low' — escalation cost scales with this")

    _OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {_OUT_JSON}")
    print(f"Wrote {_OUT_MD}")


if __name__ == "__main__":
    main()

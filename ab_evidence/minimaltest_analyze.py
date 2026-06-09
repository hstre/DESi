"""Analyze the Q4/Q8 × Raw/State minimaltest."""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ITEMS = _HERE / "results" / "minimaltest_q4_q8" / "items"
_OUT_JSON = _HERE / "results" / "minimaltest_q4_q8_summary.json"
_OUT_MD = _HERE / "reports" / "minimaltest_q4_q8_report.md"

MODEL_LABELS = {
    "ibm-granite/granite-4.1-8b": "Q8-proxy (8B)",
    "ibm-granite/granite-4.0-h-micro": "Q4-proxy (micro)",
}
PRICES = {
    "ibm-granite/granite-4.1-8b": (0.05, 0.10),
    "ibm-granite/granite-4.0-h-micro": (0.017, 0.112),
}


def get_run(item, model, variant):
    for r in item["runs"]:
        if r["model"] == model and r["variant"] == variant:
            return r
    return None


def main():
    items = [json.loads(p.read_text()) for p in sorted(_ITEMS.glob("*.json"))]
    if not items:
        print("No items.")
        return
    print(f"Loaded {len(items)} items")

    # Per-condition aggregate
    lines = ["# Q4/Q8 × Raw/DESi-State — Minimaltest\n",
             f"N = {len(items)} items, stratified across 6 LongMemEval question types.\n",
             "**Conditions:**\n",
             "- A: 8B + raw context (\"Q8 + raw\")",
             "- B: micro + raw context (\"Q4 + raw\")",
             "- C: 8B + state (evidence sessions only — oracle DESi-state)",
             "- D: micro + state\n",
             "## Overall (mean score, substring match)\n",
             "| Model | Variant | Score | a-Errors |",
             "| --- | --- | --- | --- |"]
    summary = {"N": len(items), "by_condition": {}, "by_question_type": {}}
    for model in MODEL_LABELS:
        for variant in ("raw", "state"):
            runs = [get_run(it, model, variant) for it in items]
            scores = [r["score"] for r in runs if r]
            errors = sum(1 for r in runs if r and r.get("error"))
            mean = round(st.mean(scores), 3) if scores else 0.0
            summary["by_condition"][f"{MODEL_LABELS[model]}__{variant}"] = {
                "score": mean, "errors": errors, "n": len(scores)
            }
            lines.append(f"| {MODEL_LABELS[model]} | {variant} | {mean:.3f} | {errors}/{len(scores)} |")

    # Critical comparison: D (Q4+state) vs A (Q8+raw)
    a = summary["by_condition"]["Q8-proxy (8B)__raw"]["score"]
    d = summary["by_condition"]["Q4-proxy (micro)__state"]["score"]
    lines += ["",
              "## Critical: Q4+State vs Q8+Raw\n",
              f"- **Q8 + raw context (A):** {a:.3f}",
              f"- **Q4 + DESi-state (D):** {d:.3f}",
              f"- **Δ (D − A):** {d - a:+.3f}",
              ""]
    if d >= a:
        lines.append("**Q4+State ≥ Q8+Raw — strong signal: smaller model + state matches bigger model + raw.**")
    else:
        lines.append(f"Q4+State below Q8+Raw by {a - d:.3f}. Gap may close with proper "
                     "(non-oracle) DESi-state extraction; this oracle test is upper-bound.")

    # Per-question-type
    by_type = defaultdict(list)
    for it in items:
        by_type[it["question_type"]].append(it)
    lines += ["", "## Per question type\n",
              "| Type | n | 8B raw | micro raw | 8B state | micro state |",
              "| --- | --- | --- | --- | --- | --- |"]
    for qt in sorted(by_type):
        its = by_type[qt]
        cells = {}
        for model in MODEL_LABELS:
            for v in ("raw", "state"):
                runs = [get_run(it, model, v) for it in its]
                cells[(model, v)] = round(st.mean([r["score"] for r in runs if r]), 3)
        summary["by_question_type"][qt] = {
            "n": len(its),
            "8b_raw": cells[("ibm-granite/granite-4.1-8b", "raw")],
            "micro_raw": cells[("ibm-granite/granite-4.0-h-micro", "raw")],
            "8b_state": cells[("ibm-granite/granite-4.1-8b", "state")],
            "micro_state": cells[("ibm-granite/granite-4.0-h-micro", "state")],
        }
        lines.append(f"| {qt} | {len(its)} | "
                     f"{cells[('ibm-granite/granite-4.1-8b','raw')]:.2f} | "
                     f"{cells[('ibm-granite/granite-4.0-h-micro','raw')]:.2f} | "
                     f"{cells[('ibm-granite/granite-4.1-8b','state')]:.2f} | "
                     f"{cells[('ibm-granite/granite-4.0-h-micro','state')]:.2f} |")

    # Tokens & cost
    lines += ["", "## Tokens, latency, cost\n",
              "| Model | Variant | mean in tokens | mean out tokens | mean latency ms | sum in | sum out | cost $ |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    total_cost = 0.0
    for model, (in_p, out_p) in PRICES.items():
        for v in ("raw", "state"):
            runs = [get_run(it, model, v) for it in items]
            in_t = [r.get("input_tokens") for r in runs if r and r.get("input_tokens")]
            out_t = [r.get("output_tokens") for r in runs if r and r.get("output_tokens")]
            lat = [r.get("latency_ms") for r in runs if r and r.get("latency_ms")]
            cost = sum(in_t) / 1e6 * in_p + sum(out_t) / 1e6 * out_p
            total_cost += cost
            lines.append(
                f"| {MODEL_LABELS[model]} | {v} | "
                f"{round(st.mean(in_t)) if in_t else 0} | "
                f"{round(st.mean(out_t)) if out_t else 0} | "
                f"{round(st.mean(lat)) if lat else 0} | "
                f"{sum(in_t)} | {sum(out_t)} | ${cost:.4f} |"
            )
    lines.append(f"\n**Total cost: ${total_cost:.3f}**\n")
    summary["total_cost_usd"] = round(total_cost, 4)

    _OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {_OUT_MD} and {_OUT_JSON}")
    print(f"Total cost: ${total_cost:.3f}")


if __name__ == "__main__":
    main()

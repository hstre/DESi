"""Analyze RULER-Extended A/B results — final report."""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ITEMS = _HERE / "results" / "ruler_ext_bench" / "items"
_REPORT = _HERE / "reports" / "ruler_ext_bench_report.md"
_SUMMARY = _HERE / "results" / "ruler_ext_bench_summary.json"


def get(it, model, variant):
    for r in it["runs"]:
        if r["model"] == model and r["variant"] == variant:
            return r


def main():
    items = [json.loads(p.read_text()) for p in sorted(_ITEMS.glob("*.json"))]
    if not items:
        print("No items found — run ruler_ext_run.py first.")
        return

    print(f"Loaded {len(items)} items")

    by_length = defaultdict(list)
    for it in items:
        by_length[it["length"]].append(it)

    summary = {"N": len(items), "by_length": {}}
    lines = ["# RULER-Extended A/B Results (32k / 64k / 131k)\n",
             f"Total items: {len(items)}\n",
             "## Per length × task × model × variant\n",
             "| length | task | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]

    for length in sorted(by_length, key=int):
        by_task = defaultdict(list)
        for it in by_length[length]:
            by_task[it["task"]].append(it)
        ll_summary = {}
        for task in sorted(by_task):
            its = by_task[task]
            ds_a = [get(it, "deepseek/deepseek-v4-pro", "A")["score"] for it in its]
            ds_b = [get(it, "deepseek/deepseek-v4-pro", "B")["score"] for it in its]
            gr_a = [get(it, "ibm-granite/granite-4.1-8b", "A")["score"] for it in its]
            gr_b = [get(it, "ibm-granite/granite-4.1-8b", "B")["score"] for it in its]
            row = {"n": len(its),
                   "ds_a": round(st.mean(ds_a), 3), "ds_b": round(st.mean(ds_b), 3),
                   "gr_a": round(st.mean(gr_a), 3), "gr_b": round(st.mean(gr_b), 3),
                   "delta_ds": round(st.mean(ds_b) - st.mean(ds_a), 3),
                   "delta_gr": round(st.mean(gr_b) - st.mean(gr_a), 3)}
            ll_summary[task] = row
            lines.append(f"| {length} | {task} | {row['n']} | {row['ds_a']} | {row['ds_b']} | "
                         f"{row['delta_ds']:+.3f} | {row['gr_a']} | {row['gr_b']} | "
                         f"{row['delta_gr']:+.3f} |")
        summary["by_length"][length] = ll_summary

    lines += ["", "## Per length (mean across tasks)\n",
              "| length | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    by_length_agg = {}
    for length in sorted(by_length, key=int):
        its = by_length[length]
        ds_a = [get(it, "deepseek/deepseek-v4-pro", "A")["score"] for it in its]
        ds_b = [get(it, "deepseek/deepseek-v4-pro", "B")["score"] for it in its]
        gr_a = [get(it, "ibm-granite/granite-4.1-8b", "A")["score"] for it in its]
        gr_b = [get(it, "ibm-granite/granite-4.1-8b", "B")["score"] for it in its]
        agg = {"n": len(its),
               "ds_a": round(st.mean(ds_a), 3), "ds_b": round(st.mean(ds_b), 3),
               "gr_a": round(st.mean(gr_a), 3), "gr_b": round(st.mean(gr_b), 3),
               "delta_ds": round(st.mean(ds_b) - st.mean(ds_a), 3),
               "delta_gr": round(st.mean(gr_b) - st.mean(gr_a), 3)}
        by_length_agg[length] = agg
        lines.append(f"| {length} | {agg['n']} | "
                     f"{agg['ds_a']:.3f} | {agg['ds_b']:.3f} | {agg['delta_ds']:+.3f} | "
                     f"{agg['gr_a']:.3f} | {agg['gr_b']:.3f} | {agg['delta_gr']:+.3f} |")
    summary["by_length_aggregate"] = by_length_agg

    # Error rate per model x variant x length (HTTP / context-overflow tracking)
    lines += ["", "## Error rate per (model, variant, length)\n",
              "| length | model | variant | error_rate | n_errors |",
              "| --- | --- | --- | --- | --- |"]
    err_summary = {}
    for length in sorted(by_length, key=int):
        its = by_length[length]
        for model in ("deepseek/deepseek-v4-pro", "ibm-granite/granite-4.1-8b"):
            for v in ("A", "B"):
                runs = [get(it, model, v) for it in its]
                errs = [r for r in runs if r.get("error")]
                rate = len(errs) / len(runs) if runs else 0
                err_summary[f"{length}_{model}_{v}"] = {"rate": round(rate, 3),
                                                        "n_errors": len(errs),
                                                        "n_total": len(runs)}
                lines.append(f"| {length} | {model.split('/')[-1]} | {v} | "
                             f"{rate:.2%} | {len(errs)}/{len(runs)} |")
    summary["errors"] = err_summary

    # Costs
    lines += ["", "## Tokens & cost\n"]
    PRICES = {"deepseek/deepseek-v4-pro": (0.43, 0.87),
              "ibm-granite/granite-4.1-8b": (0.05, 0.10)}
    total_cost = 0
    lines += ["| model | variant | mean_in | sum_in | sum_out | cost_$ |",
              "| --- | --- | --- | --- | --- | --- |"]
    for model, (in_p, out_p) in PRICES.items():
        for v in ("A", "B"):
            runs = [get(it, model, v) for it in items]
            in_t = [r.get("input_tokens") for r in runs if r.get("input_tokens")]
            out_t = [r.get("output_tokens") for r in runs if r.get("output_tokens")]
            c = sum(in_t)/1e6*in_p + sum(out_t)/1e6*out_p
            total_cost += c
            lines.append(f"| {model.split('/')[-1]} | {v} | "
                         f"{round(st.mean(in_t)) if in_t else 0} | "
                         f"{sum(in_t)} | {sum(out_t)} | ${c:.3f} |")
    lines.append(f"\nTotal cost: **${total_cost:.2f}**\n")
    summary["total_cost_usd"] = round(total_cost, 4)

    _SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {_REPORT} and {_SUMMARY}")
    print(f"\nTotal cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()

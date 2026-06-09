"""Analyze the v2 minimaltest: 8 conditions (2 models × {raw, oracle, desi-llm, desi-emb})."""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ITEMS = _HERE / "results" / "minimaltest_q4_q8_v2" / "items"
_OUT_JSON = _HERE / "results" / "minimaltest_q4_q8_v2_summary.json"
_OUT_MD = _HERE / "reports" / "minimaltest_q4_q8_v2_report.md"

LABELS = {
    "ibm-granite/granite-4.1-8b": "Q8 (8B)",
    "ibm-granite/granite-4.0-h-micro": "Q4 (micro)",
}
PRICES = {
    "ibm-granite/granite-4.1-8b": (0.05, 0.10),
    "ibm-granite/granite-4.0-h-micro": (0.017, 0.112),
}
STATE_LABELS = {
    "raw": "Volltext",
    "oracle": "Oracle-State",
    "desi_llm": "DESi-LLM",
    "desi_emb": "DESi-Embedding",
}


def get_run(item, model, state_type):
    for r in item["runs"]:
        rstate = r.get("state_type") or r.get("variant")
        # v1 used "raw" and "state" (= oracle); v2 uses raw/oracle/desi_llm/desi_emb
        if r.get("model") == model and rstate == state_type:
            return r
        # fallback: state == oracle
        if r.get("model") == model and state_type == "oracle" and rstate == "state":
            return r
    return None


def main():
    items = sorted(_ITEMS.glob("*.json"))
    if not items:
        print("No items.")
        return
    items = [json.loads(p.read_text()) for p in items]
    print(f"Loaded {len(items)} items")

    # Filter scorable (excl. single-session-preference which is non-scorable by substring)
    scorable = [it for it in items if it["question_type"] != "single-session-preference"]

    lines = ["# Q4/Q8 × {Raw, Oracle, DESi-LLM, DESi-Emb} — Extended Factor Analysis\n",
             f"N total: {len(items)} · N scorable (excl. single-session-preference): {len(scorable)}\n",
             "## Setup\n",
             "- **Q8 (groß)**: `ibm-granite/granite-4.1-8b` (8B Params)",
             "- **Q4 (klein)**: `ibm-granite/granite-4.0-h-micro` (~3B Klasse, Hybrid Micro)",
             "- **Raw**: Volle Konversations-Historie (~100k Tokens)",
             "- **Oracle**: Nur die Sessions, die laut Ground-Truth die Antwort enthalten (~5k Tokens)",
             "- **DESi-LLM**: micro liest Konversation + Frage, gibt Fact-Liste aus. Answerer sieht NUR die Facts.",
             "- **DESi-Emb**: Top-k Sessions per `all-MiniLM-L6-v2` Cosine-Similarity zur Frage. k = #evidence sessions (size-matched zu Oracle).\n",
             "## Hauptergebnis: Substring-Score auf scorbarer Subset\n",
             "| State-Typ | Q4 (micro) | Q8 (8B) |",
             "| --- | --- | --- |"]

    summary = {"N": len(items), "N_scorable": len(scorable),
               "by_state_model": {}, "by_question_type": {},
               "desi_emb_evidence_recall": []}

    state_order = ["raw", "oracle", "desi_llm", "desi_emb"]
    for state in state_order:
        cells = {}
        for model in LABELS:
            runs = [get_run(it, model, state) for it in scorable]
            scores = [r["score"] for r in runs if r and r.get("score") is not None]
            cells[model] = round(st.mean(scores), 3) if scores else None
            summary["by_state_model"][f"{LABELS[model]}__{state}"] = cells[model]
        q4 = cells.get("ibm-granite/granite-4.0-h-micro")
        q8 = cells.get("ibm-granite/granite-4.1-8b")
        lines.append(f"| {STATE_LABELS[state]} | {q4 if q4 is not None else '—'} | {q8 if q8 is not None else '—'} |")

    # The key comparisons
    q8_raw = summary["by_state_model"]["Q8 (8B)__raw"]
    q4_oracle = summary["by_state_model"]["Q4 (micro)__oracle"]
    q4_llm = summary["by_state_model"]["Q4 (micro)__desi_llm"]
    q4_emb = summary["by_state_model"]["Q4 (micro)__desi_emb"]

    if q8_raw is not None:
        lines += ["\n## Kernhypothese: Q4 + DESi-State ≥ Q8 + Raw\n",
                  f"- **Q8 + Raw (Baseline):** {q8_raw}",
                  f"- **Q4 + Oracle-State (obere Schranke):** {q4_oracle} (Δ {q4_oracle - q8_raw:+.3f})",
                  f"- **Q4 + DESi-LLM:** {q4_llm} (Δ {q4_llm - q8_raw:+.3f})",
                  f"- **Q4 + DESi-Embedding:** {q4_emb} (Δ {q4_emb - q8_raw:+.3f})"]

        gap_oracle_to_baseline = q4_oracle - q8_raw
        if gap_oracle_to_baseline > 0:
            llm_retention = (q4_llm - q8_raw) / gap_oracle_to_baseline * 100
            emb_retention = (q4_emb - q8_raw) / gap_oracle_to_baseline * 100
            lines.append(f"\n**DESi-Vorteil-Retention** (Anteil des Oracle-Vorteils über Baseline, "
                         "den die Auto-Extraktion erreicht):")
            lines.append(f"- DESi-LLM retention: **{llm_retention:.0f}%** des Oracle-Vorteils")
            lines.append(f"- DESi-Emb retention: **{emb_retention:.0f}%** des Oracle-Vorteils")
            summary["llm_retention_pct"] = round(llm_retention, 1)
            summary["emb_retention_pct"] = round(emb_retention, 1)

    # Embedding evidence recall
    recalls = []
    for it in items:
        e = it.get("extractions", {}).get("desi_emb", {})
        if "evidence_recall" in e:
            recalls.append(e["evidence_recall"])
    if recalls:
        summary["desi_emb_evidence_recall"] = {
            "mean": round(st.mean(recalls), 3),
            "min": round(min(recalls), 3),
            "max": round(max(recalls), 3),
        }
        lines.append(f"\n**DESi-Embedding evidence recall** (% Oracle-Sessions, die top-k wählte): "
                     f"mean={st.mean(recalls):.2%}, range=[{min(recalls):.0%}, {max(recalls):.0%}]")

    # Per-question-type
    lines += ["\n## Per Question-Type (mean score)\n",
              "| Type | n | Q4 raw | Q4 oracle | Q4 desi-llm | Q4 desi-emb | Q8 raw | Q8 oracle | Q8 desi-llm | Q8 desi-emb |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    by_type = defaultdict(list)
    for it in items:
        by_type[it["question_type"]].append(it)
    for qt in sorted(by_type):
        its = by_type[qt]
        cells = {}
        for model in LABELS:
            for state in state_order:
                runs = [get_run(it, model, state) for it in its]
                scores = [r["score"] for r in runs if r and r.get("score") is not None]
                cells[(model, state)] = round(st.mean(scores), 2) if scores else None
        summary["by_question_type"][qt] = {
            f"{LABELS[m]}__{s}": cells[(m, s)] for m in LABELS for s in state_order
        }
        def fmt(v):
            return str(v) if v is not None else "—"
        row = [qt, str(len(its))]
        for m in ["ibm-granite/granite-4.0-h-micro", "ibm-granite/granite-4.1-8b"]:
            for s in state_order:
                row.append(fmt(cells.get((m, s))))
        lines.append("| " + " | ".join(row) + " |")

    # Tokens, latency, cost
    lines += ["\n## Tokens, Latency, Kosten\n",
              "| Modell | State | mean in | mean out | mean latency | sum in | sum out | cost $ |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    total_cost = 0.0
    extractor_cost = 0.0
    for model, (in_p, out_p) in PRICES.items():
        for state in state_order:
            runs = [get_run(it, model, state) for it in items]
            in_t = [r.get("input_tokens") for r in runs if r and r.get("input_tokens")]
            out_t = [r.get("output_tokens") for r in runs if r and r.get("output_tokens")]
            lat = [r.get("latency_ms") for r in runs if r and r.get("latency_ms")]
            if not in_t:
                continue
            c = sum(in_t)/1e6*in_p + sum(out_t)/1e6*out_p
            total_cost += c
            lines.append(
                f"| {LABELS[model]} | {STATE_LABELS[state]} | "
                f"{round(st.mean(in_t)) if in_t else 0} | "
                f"{round(st.mean(out_t)) if out_t else 0} | "
                f"{round(st.mean(lat)/1000, 1) if lat else 0}s | "
                f"{sum(in_t)} | {sum(out_t)} | ${c:.4f} |"
            )

    # Extractor cost
    extractor_in = sum(it.get("extractions", {}).get("desi_llm", {}).get("extractor_input_tokens", 0) or 0
                       for it in items)
    extractor_out = sum(it.get("extractions", {}).get("desi_llm", {}).get("extractor_output_tokens", 0) or 0
                        for it in items)
    extractor_cost = extractor_in / 1e6 * 0.017 + extractor_out / 1e6 * 0.112
    total_cost += extractor_cost
    if extractor_in > 0:
        lines.append(f"| Q4 (micro) extractor | DESi-LLM | "
                     f"{round(extractor_in/max(1,len(items)))} | "
                     f"{round(extractor_out/max(1,len(items)))} | — | "
                     f"{extractor_in} | {extractor_out} | ${extractor_cost:.4f} |")

    lines.append(f"\n**Total cost (this run): ${total_cost:.3f}**")
    summary["total_cost_usd"] = round(total_cost, 4)
    summary["extractor_cost_usd"] = round(extractor_cost, 4)

    _OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    _OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {_OUT_MD}")
    print(f"\nTotal cost: ${total_cost:.3f}")


if __name__ == "__main__":
    main()

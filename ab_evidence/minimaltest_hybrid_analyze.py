"""Analyze the hybrid evidence-grounded extractor results vs prior baselines."""
from __future__ import annotations

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HYBRID = _HERE / "results" / "minimaltest_hybrid" / "items"
_V2 = _HERE / "results" / "minimaltest_q4_q8_v2" / "items"
_OUT_MD = _HERE / "reports" / "minimaltest_hybrid_report.md"
_OUT_JSON = _HERE / "results" / "minimaltest_hybrid_summary.json"

LABELS = {
    "ibm-granite/granite-4.1-8b": "Q8 (8B)",
    "ibm-granite/granite-4.0-h-micro": "Q4 (micro)",
}


def get_run(item, model, state_type):
    for r in item["runs"]:
        rstate = r.get("state_type") or r.get("variant")
        if r.get("model") == model:
            if rstate == state_type:
                return r
            if state_type == "oracle" and rstate == "state":
                return r
    return None


def main():
    hybrid_items = sorted(_HYBRID.glob("*.json"))
    if not hybrid_items:
        print("No hybrid items.")
        return
    hybrid_items = [json.loads(p.read_text()) for p in hybrid_items]
    v2_items = {json.loads(p.read_text())["question_id"]: json.loads(p.read_text()) for p in _V2.glob("*.json")}

    scorable = [it for it in hybrid_items if it["question_type"] != "single-session-preference"]
    print(f"Loaded {len(hybrid_items)} hybrid items, {len(scorable)} scorable")

    # Compare hybrid to v2 baselines on same items
    lines = ["# Hybrid Evidence-Grounded Extractor — Results\n",
             f"N={len(hybrid_items)} (scorbar: {len(scorable)}, excl. single-session-preference)\n",
             "## Pipeline\n",
             "1. **Embedding top-10**: `all-MiniLM-L6-v2` cosine sim zwischen Frage und allen Sessions, top-10 ausgewählt",
             "2. **Per-Session LLM-Extraktion**: micro extrahiert pro Session bis zu 4 Evidence-Cards `{claim, quote}`",
             "3. **Anti-Hallucination Validierung**: Quote muss verbatim Substring der Session sein, sonst verworfen",
             "4. **Chronologisches Ordering**: Cards in Session-Reihenfolge (oldest first) zum Answerer",
             "5. **Answerer**: Q4 oder Q8 sieht NUR die validierten, geordneten Cards\n",
             "## Hauptergebnis\n",
             "| State-Typ | Q4 (micro) | Q8 (8B) |",
             "| --- | --- | --- |"]

    summary = {"N": len(hybrid_items), "N_scorable": len(scorable), "by_state_model": {}}

    # Pull v2 baselines on the same scorable items
    state_order = ["raw", "oracle", "desi_llm", "desi_emb", "hybrid"]
    state_labels = {"raw": "Volltext", "oracle": "Oracle-State", "desi_llm": "DESi-LLM (v2)",
                    "desi_emb": "DESi-Emb (v2)", "hybrid": "Hybrid (NEU)"}

    for state in state_order:
        cells = {}
        for model in LABELS:
            scores = []
            if state == "hybrid":
                for it in scorable:
                    r = get_run(it, model, "hybrid")
                    if r and r.get("score") is not None:
                        scores.append(r["score"])
            else:
                for it in scorable:
                    v2 = v2_items.get(it["question_id"])
                    if v2:
                        r = get_run(v2, model, state)
                        if r and r.get("score") is not None:
                            scores.append(r["score"])
            cells[model] = round(st.mean(scores), 3) if scores else None
            summary["by_state_model"][f"{LABELS[model]}__{state}"] = cells[model]
        q4 = cells.get("ibm-granite/granite-4.0-h-micro")
        q8 = cells.get("ibm-granite/granite-4.1-8b")
        lines.append(f"| {state_labels[state]} | {q4 if q4 is not None else '—'} | {q8 if q8 is not None else '—'} |")

    # Key comparison
    q8_raw = summary["by_state_model"].get("Q8 (8B)__raw")
    q4_oracle = summary["by_state_model"].get("Q4 (micro)__oracle")
    q4_hybrid = summary["by_state_model"].get("Q4 (micro)__hybrid")
    q4_llm = summary["by_state_model"].get("Q4 (micro)__desi_llm")
    q4_emb = summary["by_state_model"].get("Q4 (micro)__desi_emb")

    if q8_raw is not None and q4_oracle is not None and q4_hybrid is not None:
        gap = q4_oracle - q8_raw
        hybrid_delta = q4_hybrid - q8_raw
        retention = (hybrid_delta / gap * 100) if gap > 0 else None
        lines += ["",
                  "## Hypothese: Q4 + Hybrid-State ≥ Q8 + Raw\n",
                  f"- **Q8 + Raw (Baseline):** {q8_raw}",
                  f"- **Q4 + Oracle (obere Schranke):** {q4_oracle} (Δ {q4_oracle - q8_raw:+.3f})",
                  f"- **Q4 + DESi-LLM (v2):** {q4_llm} (Δ {(q4_llm - q8_raw):+.3f})",
                  f"- **Q4 + DESi-Embedding (v2):** {q4_emb} (Δ {(q4_emb - q8_raw):+.3f})",
                  f"- **Q4 + Hybrid (NEU):** {q4_hybrid} (Δ {hybrid_delta:+.3f})"]
        if retention is not None:
            lines.append(f"\n**Hybrid-Retention: {retention:.0f}% des Oracle-Vorteils**")
            summary["hybrid_retention_pct"] = round(retention, 1)
            if retention >= 70:
                lines.append("\n**Schwellenwert 70% erreicht — Hypothese gestützt.**")
            elif retention >= 40:
                lines.append("\n**Teil-Erfolg: signifikanter Vorteil, aber unter 70%-Schwelle.**")
            else:
                lines.append("\n**Schwellenwert verfehlt — Hybrid liefert kaum besser als Vorgänger.**")

    # Extraction quality diagnostics
    lines += ["", "## Extraktions-Diagnostik\n"]
    n_cards_total = []
    sessions_with_cards = []
    rejected_per_session = []
    evidence_recall = []
    for it in hybrid_items:
        hx = it.get("hybrid_extraction", {})
        n_cards_total.append(hx.get("n_cards_total", 0))
        evidence_recall.append(hx.get("evidence_recall", 0))
        per_sess = hx.get("per_session", [])
        sessions_with_cards.append(sum(1 for s in per_sess if s.get("cards_validated", 0) > 0))
        for s in per_sess:
            rejected_per_session.append(s.get("cards_rejected_for_hallucination", 0))
    lines.append(f"- Cards pro Item: mean {st.mean(n_cards_total):.1f}, median {st.median(n_cards_total):.0f}, max {max(n_cards_total)}")
    lines.append(f"- Sessions mit ≥1 validierter Card (von 10): mean {st.mean(sessions_with_cards):.1f}")
    lines.append(f"- Halluzinierte Cards (Quote nicht verbatim): total {sum(rejected_per_session)}, mean/session {st.mean(rejected_per_session):.2f}")
    lines.append(f"- Embedding evidence recall (top-10): mean {st.mean(evidence_recall):.2%}")
    summary["extraction_diagnostics"] = {
        "cards_per_item_mean": round(st.mean(n_cards_total), 1),
        "sessions_with_cards_mean": round(st.mean(sessions_with_cards), 1),
        "hallucinated_cards_total": sum(rejected_per_session),
        "evidence_recall_mean": round(st.mean(evidence_recall), 3),
    }

    # Per question type
    lines += ["", "## Per Question-Type (Hybrid score)\n",
              "| Type | n | Q4 hybrid | Q8 hybrid | Q4 oracle | Q8 raw |",
              "| --- | --- | --- | --- | --- | --- |"]
    by_type = defaultdict(list)
    for it in hybrid_items:
        by_type[it["question_type"]].append(it)
    for qt in sorted(by_type):
        its = by_type[qt]
        q4_h_scores = [get_run(it, "ibm-granite/granite-4.0-h-micro", "hybrid")["score"]
                       for it in its if get_run(it, "ibm-granite/granite-4.0-h-micro", "hybrid")]
        q8_h_scores = [get_run(it, "ibm-granite/granite-4.1-8b", "hybrid")["score"]
                       for it in its if get_run(it, "ibm-granite/granite-4.1-8b", "hybrid")]
        q4_o_scores = []
        q8_r_scores = []
        for it in its:
            v2 = v2_items.get(it["question_id"])
            if v2:
                r_o = get_run(v2, "ibm-granite/granite-4.0-h-micro", "oracle")
                r_r = get_run(v2, "ibm-granite/granite-4.1-8b", "raw")
                if r_o: q4_o_scores.append(r_o["score"])
                if r_r: q8_r_scores.append(r_r["score"])
        def fmt(xs):
            return f"{st.mean(xs):.2f}" if xs else "—"
        lines.append(f"| {qt} | {len(its)} | {fmt(q4_h_scores)} | {fmt(q8_h_scores)} | {fmt(q4_o_scores)} | {fmt(q8_r_scores)} |")

    # Cost
    lines += ["", "## Kosten\n"]
    # Per-session extraction calls
    extractor_in_total = 0
    extractor_out_total = 0
    answerer_in_total = defaultdict(int)
    answerer_out_total = defaultdict(int)
    for it in hybrid_items:
        for s in it.get("hybrid_extraction", {}).get("per_session", []):
            extractor_in_total += s.get("input_tokens", 0) or 0
            extractor_out_total += s.get("output_tokens", 0) or 0
        for r in it.get("runs", []):
            m = r["model"]
            answerer_in_total[m] += r.get("input_tokens", 0) or 0
            answerer_out_total[m] += r.get("output_tokens", 0) or 0

    ex_cost = extractor_in_total / 1e6 * 0.017 + extractor_out_total / 1e6 * 0.112
    a_cost_8b = answerer_in_total["ibm-granite/granite-4.1-8b"] / 1e6 * 0.05 + \
                answerer_out_total["ibm-granite/granite-4.1-8b"] / 1e6 * 0.10
    a_cost_micro = answerer_in_total["ibm-granite/granite-4.0-h-micro"] / 1e6 * 0.017 + \
                   answerer_out_total["ibm-granite/granite-4.0-h-micro"] / 1e6 * 0.112
    total = ex_cost + a_cost_8b + a_cost_micro
    lines.append(f"- Extractor calls (10 per item × {len(hybrid_items)} items): {extractor_in_total} in tokens, ${ex_cost:.4f}")
    lines.append(f"- Q8 answerer: ${a_cost_8b:.4f}")
    lines.append(f"- Q4 answerer: ${a_cost_micro:.4f}")
    lines.append(f"- **Total: ${total:.3f}**")
    summary["total_cost_usd"] = round(total, 4)
    summary["extractor_cost_usd"] = round(ex_cost, 4)

    _OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    _OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {_OUT_MD}")
    print(f"Total cost: ${total:.3f}")


if __name__ == "__main__":
    main()

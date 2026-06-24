"""Consolidated final report across all DESi ablation phases (2–5 + the k-sweep).

Pulls recall means from the committed result files and renders one multi-page landscape PDF: what
was tested, the five questions with numbers, the retrieval arc (lexical -> neural -> optimal-k ->
long-doc), the token-efficiency result, and the consolidated supported / not-supported / open lists.
Conservative; no claim beyond the data.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "reports" / "ablation_final_report.pdf"


def _load(name):
    p = _HERE / "results" / name
    return json.loads(p.read_text()) if p.exists() else None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _rc(out, cond):
    """mean recall for a condition across an out's cases, or None if absent."""
    try:
        return _mean([r["conditions"][cond]["recall"] for r in out["cases"]])
    except (KeyError, TypeError):
        return None


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Body", parent=ss["BodyText"], fontSize=8.8, leading=11.6, spaceAfter=4))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=12, spaceBefore=9, spaceAfter=3,
                          textColor=colors.HexColor("#22323f")))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.7, leading=9.6,
                          textColor=colors.HexColor("#444")))
    ss.add(ParagraphStyle("Li", parent=ss["BodyText"], fontSize=8.6, leading=11, spaceAfter=2))
    return ss


def _tbl(rows, widths, fs=8.2):
    t = Table(rows, repeatRows=1, colWidths=widths)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                           ("FONTSIZE", (0, 0), (-1, -1), fs),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbb")),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f5")])]))
    return t


def _bullets(items, ss):
    return ListFlowable([ListItem(Paragraph(t, ss["Li"]), leftIndent=8) for t in items],
                        bulletType="bullet", start="•", leftIndent=10)


def build() -> Path:
    p2 = _load("ablation2_phase2.json")                         # core (11 cond, sonnet)
    p4 = {m: _load(f"ablation2_phase4_{m}.json") for m in ("sonnet", "gpt4o", "llama")}
    p5 = {m: _load(f"ablation2_phase5_{m}.json") for m in ("sonnet", "granite")}
    ss = _ss()
    F = []

    F.append(Paragraph("DESi epistemic-state ablation — consolidated report (Phases 2–5)", ss["Title"]))
    F.append(Paragraph(
        "A falsification-oriented study of whether a DESi epistemic-state slice helps an LLM, and "
        "<i>why</i> — vs full chat, vs plausible-wrong / neutral / contradictory states, vs lexical "
        "and neural retrieval, with metadata on/off, and with the state hand-curated vs "
        "auto-constructed. Real runs (OpenRouter), temperature 0, fixed seed, 2–3 reps; 4 models "
        "(Sonnet-4.5, GPT-4o, Llama-3.3-70B, Granite-4.1-8B). The recall evaluator is paraphrase- "
        "and negation-blind (content-token Jaccard ≥ 0.25), so only RELATIVE comparisons are meant; "
        "no prompt was tuned to make any condition win. <b>Bottom line up front:</b> correct, "
        "auto-constructible state selection is load-bearing and is mainly a TOKEN-EFFICIENCY + "
        "long-document-robustness win over retrieval — not a general capability gain, and metadata "
        "governance is not established.", ss["Body"]))

    # --- the condition ladder across regimes
    F.append(Paragraph("1 · The condition ladder, recall across regimes", ss["H2b"]))
    lcols = ["A", "B", "B_auto", "C", "F", "G", "R1", "R2n", "E"]
    cmap = {"A": "A_baseline_full_context", "B": "B_normal_desi", "B_auto": "B_auto_constructed",
            "C": "C_wrong_slice", "F": "F_empty_state", "G": "G_neutral_irrelevant",
            "R1": "R1_bm25", "R2n": "R2n_neural", "E": "E_budget_matched_status_stripped"}
    rows = [["regime (model)"] + lcols]
    def _cell(v): return "—" if v is None else str(v)
    rows.append(["core short (sonnet)"] + [_cell(_rc(p2, cmap[c])) for c in lcols])
    rows.append(["lifecycle short (sonnet)"] + [_cell(_rc(p4["sonnet"], cmap[c])) for c in lcols])
    rows.append(["lifecycle short (gpt-4o)"] + [_cell(_rc(p4["gpt4o"], cmap[c])) for c in lcols])
    rows.append(["lifecycle short (llama)"] + [_cell(_rc(p4["llama"], cmap[c])) for c in lcols])
    rows.append(["lifecycle LONG ~18k (sonnet)"] + [_cell(_rc(p5["sonnet"], cmap[c])) for c in lcols])
    rows.append(["lifecycle LONG ~18k (granite)"] + [_cell(_rc(p5["granite"], cmap[c])) for c in lcols])
    F.append(_tbl(rows, [4.6 * cm] + [1.9 * cm] * len(lcols), fs=7.6))
    F.append(Paragraph("Blank = condition not run in that regime. C wrong-slice / F empty / G "
                       "neutral collapse everywhere; B and B_auto stay near 1.0.", ss["Sm"]))

    # --- five questions
    F.append(Paragraph("2 · The five questions", ss["H2b"]))
    F.append(_bullets([
        "<b>Q1 Is correct state SELECTION load-bearing? YES (strong).</b> Wrong-slice C, empty F and "
        "neutral G all collapse to ~0 recall while B ≈ 1.0 — across every regime and all 4 models. A "
        "plausible-but-wrong state is no better than no state, and worse on degeneration.",
        "<b>Q2 Does wrong state POISON? YES — visible in degeneration, not recall.</b> On recall "
        "F≈G≈C (~0); the degeneration metrics separate them: C adopts the wrong case's claims "
        "(invalid-reuse ≈ 9–15, bad-framing 1.0), G is pulled into irrelevant content (≈ 3–8), H "
        "(contradiction) loops and reuses contradictions. Injected claims PERSIST and even RELAPSE "
        "across neutral double-check probes (C: dropped when probed, then reverted). The model is "
        "CONFIDENTLY wrong (self-reported confidence 93–100 while recall ~0).",
        "<b>Q3 Does the metadata GOVERNANCE help? NOT established.</b> Budget-matched B−E ≈ 0 in "
        "every phase and every model (the category typing / IDs add no measurable recall over the "
        "same texts at the same budget). The value is the SELECTION, not the typing.",
        "<b>Q4 Does DESi beat RETRIEVAL? Yes, but the honest size depends on the retriever and the "
        "document length (see §3).</b>",
        "<b>Q5 Can the state be AUTO-CONSTRUCTED? YES.</b> One LLM extraction pass that resolves "
        "supersession yields B_auto ≈ B (B−B_auto ≈ +0.04..+0.13, within noise), worst single case "
        "0.80, on all models — and it survives long documents (B_auto 0.88–0.96 at ~18k tokens). So "
        "the Phase-3 'curated-GT' caveat is substantially addressed: the value is constructible, even "
        "by a small model (Granite).",
    ], ss))

    # --- retrieval arc
    F.append(Paragraph("3 · The DESi-vs-retrieval arc (the most nuanced result)", ss["H2b"]))
    arc = [["retriever / regime", "B − retrieval (recall)", "reading"],
           ["lexical BM25/TF-IDF, short docs (P3)", "≈ +0.70", "lexical retrieval overstated DESi's edge"],
           ["neural bge-small, budget-matched, short (P4)", "≈ +0.15 .. +0.28", "a good dense retriever closes most of the gap"],
           ["neural, OPTIMAL k≈all chunks, short (k-sweep)", "≈ +0.05", "at unlimited budget retrieval ≈ DESi"],
           ["budget-matched, LONG ~18k docs (P5)", "BM25 +0.5 · neural +0.9", "retrieval collapses; DESi holds at ~2% of tokens"]]
    F.append(_tbl(arc, [7.0 * cm, 4.6 * cm, 7.2 * cm], fs=8.0))
    F.append(Paragraph(
        "The k-sweep (Sonnet, 8 short cases) is the key to reading this: neural recall ran 0.15 (k=1) "
        "→ 0.83 (k≈13, 1× B budget) → 0.95 (k≈18 ≈ all chunks). So on SHORT chats retrieval matches "
        "DESi <i>if given enough k</i>, which is cheap there — meaning DESi's short-doc edge is mostly "
        "TOKEN EFFICIENCY (same recall, ~13 chunks vs a 372-token slice), not capability. On LONG "
        "documents 'all chunks' does not fit the budget: at 1% of ~990 chunks the small embedder is "
        "fooled by generically-relevant filler (it retrieves 'how is X set up' over the actual "
        "decision turns; BM25's keyword match is more robust), so retrieval collapses while DESi/B_auto "
        "stay near 1.0. <i>Honest caveat:</i> the neural collapse is for a SMALL embedder (bge-small "
        "384d) + a generic-task query; a stronger embedder would rank needles better, so B−R1 ≈ +0.5 is "
        "the more representative long-doc gap.", ss["Body"]))

    # --- token efficiency
    F.append(Paragraph("4 · Token efficiency (the clearest practical win)", ss["H2b"]))
    a_tok = _mean([r["conditions"]["A_baseline_full_context"]["input_token_estimate"] for r in p5["sonnet"]["cases"]])
    b_tok = _mean([r["conditions"]["B_normal_desi"]["input_token_estimate"] for r in p5["sonnet"]["cases"]])
    F.append(Paragraph(
        f"On the ~18k-token documents, B (DESi) scored 1.0 / 0.96 (Sonnet / Granite) on <b>~{b_tok:.0f} "
        f"input tokens</b>, while the full chat A scored 0.88 / 0.76 on <b>~{a_tok:.0f} tokens</b> "
        f"(~{a_tok / b_tok:.0f}× more) — i.e. DESi gives <b>better-than-full-context recall at ~1/{a_tok / b_tok:.0f} "
        "of the cost</b>, and B_auto nearly matches it. This is the most robust, least-caveated finding.",
        ss["Body"]))

    # --- conclusions
    F.append(Paragraph("5 · Consolidated conclusions", ss["H2b"]))
    F.append(Paragraph("<b>Supported by the data:</b>", ss["Body"]))
    F.append(_bullets([
        "Correct, AUTO-CONSTRUCTIBLE epistemic-state selection is load-bearing.",
        "Plausible-wrong / neutral / contradictory structure is actively toxic, sticky (persists & "
        "relapses) and produces confidently-wrong output — detectable only via degeneration metrics.",
        "DESi's advantage over retrieval is TOKEN EFFICIENCY (full-context-or-better recall at ~2% of "
        "tokens) + ROBUSTNESS on long documents where budget retrieval cannot fit/find the needles.",
        "Confidently-reporting-stale is primarily a RETRIEVAL pathology; the resolved state removes it.",
    ], ss))
    F.append(Paragraph("<b>NOT supported / explicitly not claimed:</b>", ss["Body"]))
    F.append(_bullets([
        "'DESi makes the model smarter' / 'DESi wins generally' — no general capability gain; at "
        "unlimited budget a good neural retriever ≈ DESi on short tasks.",
        "Metadata governance (typing/IDs) — B ≈ E everywhere; not established.",
        "A large absolute-capability gap vs strong retrieval — the lexical ~0.7 was an artefact.",
    ], ss))
    F.append(Paragraph("<b>Open:</b> a held-out extractor model for B_auto (avoid self-circularity); "
                       "a stronger neural retriever for the long-doc gap; harder multi-supersession "
                       "chains; larger N (15–20+) to tighten the borderline short-doc B−R2n CI.", ss["Body"]))

    # --- limitations + repro
    F.append(Paragraph("6 · Limitations & reproduce", ss["H2b"]))
    F.append(Paragraph(
        "Small N per regime (2–8 cases); paraphrase/negation-blind evaluator (relative only; recall is "
        "unreliable for the contradiction condition H); B_auto extractor = same model family as the "
        "summariser; long-doc filler is synthetic; self-confidence is self-reported, not logprobs. "
        "All conditions/metrics are unit-tested; runs are temp-0 + seeded; results store metrics only "
        "(no raw model text, no API key). Reproduce: <font face='Courier'>export OPENROUTER_API_KEY=…; "
        "python ab_evidence/ablation_run2.py</font> ; build PDFs via "
        "<font face='Courier'>ab_evidence/build_phase{2..5}_pdf.py</font>. Total spend across all "
        "phases ≈ a few USD.", ss["Sm"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4), title="DESi ablation — consolidated report",
                      leftMargin=1.3 * cm, rightMargin=1.3 * cm, topMargin=1.1 * cm,
                      bottomMargin=1.0 * cm).build(F)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

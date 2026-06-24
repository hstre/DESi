"""Phase-5 PDF: long documents (~18k tok), 2 models (Sonnet-4.5 + Granite-4.1-8B). Reads results/
ablation2_phase5_{sonnet,granite}.json. Shows the long-context regime where budget-matched retrieval
collapses and DESi's token efficiency is decisive. Conservative; caveats stated."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "reports" / "ablation2_phase5.pdf"
_MODELS = [("phase5_sonnet", "Sonnet-4.5 (large)"), ("phase5_granite", "Granite-4.1-8B (small)")]
_SHORT = {"A_baseline_full_context": "A full-chat", "B_normal_desi": "B DESi",
          "B_auto_constructed": "B_auto", "R1_bm25": "R1 bm25", "R2n_neural": "R2n neural",
          "E_budget_matched_status_stripped": "E"}


def _load(tag):
    return json.loads((_HERE / "results" / f"ablation2_{tag}.json").read_text())


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("B2", parent=ss["BodyText"], fontSize=8.7, leading=11.5, spaceAfter=4))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.6, leading=9.5,
                          textColor=colors.HexColor("#444")))
    return ss


def _tbl(rows, widths, fs=8.3):
    t = Table(rows, repeatRows=1, colWidths=widths)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                           ("FONTSIZE", (0, 0), (-1, -1), fs),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbb")),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")])]))
    return t


def _m(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def build() -> Path:
    outs = {lbl: _load(tag) for tag, lbl in _MODELS}
    conds = next(iter(outs.values()))["conditions"]
    ss = _ss()
    flow = [Paragraph("DESi ablation Phase-5 — LONG documents (~18k tok), large + small model", ss["Title"]),
            Paragraph("Real run · temp 0 · 2 reps · 5 lifecycle/supersession cases padded to ~18k "
                      "tokens (the reversed decision + ruled-out item buried in ~990 distractor "
                      "turns). Now the budget-match BINDS: A sees the full ~18k chat; B / retrieval "
                      "get ~372 tokens, so retrieval can pack only 8–9 of ~990 chunks (~1%). "
                      "Sonnet-4.5 + Granite-4.1-8B. Conservative.", ss["B2"])]

    flow.append(Paragraph("Mean recall (5 cases) — and input tokens", ss["H2b"]))
    rows = [["model"] + [_SHORT[c] for c in conds] + ["A tok", "B tok"]]
    for lbl, out in outs.items():
        rows.append([lbl] + [str(_m([r["conditions"][c]["recall"] for r in out["cases"]])) for c in conds]
                    + [f"{_m([r['conditions']['A_baseline_full_context']['input_token_estimate'] for r in out['cases']]):.0f}",
                       f"{_m([r['conditions']['B_normal_desi']['input_token_estimate'] for r in out['cases']]):.0f}"])
    flow.append(_tbl(rows, [4.2 * cm] + [2.0 * cm] * len(conds) + [1.7 * cm, 1.5 * cm]))

    flow.append(Paragraph("Key deltas (mean recall over 5 cases)", ss["H2b"]))
    pairs = [("B_normal_desi", "A_baseline_full_context", "DESi vs full chat (49× fewer tokens)"),
             ("B_normal_desi", "R1_bm25", "vs BM25 at 1% budget"),
             ("B_normal_desi", "R2n_neural", "vs small-neural at 1% budget"),
             ("B_normal_desi", "B_auto_constructed", "DESi vs AUTO-built DESi"),
             ("A_baseline_full_context", "R2n_neural", "full chat vs budget retrieval")]
    drows = [["comparison", "note"] + [lbl.split(" ")[0] for _, lbl in _MODELS]]
    for x, y, note in pairs:
        cells = [f"{_m([r['conditions'][x]['recall'] - r['conditions'][y]['recall'] for r in outs[lbl]['cases']]):+.2f}"
                 for _, lbl in _MODELS]
        drows.append([f"{_SHORT[x].split()[0]} − {_SHORT[y].split()[0]}", note] + cells)
    flow.append(_tbl(drows, [2.8 * cm, 6.0 * cm, 3.0 * cm, 3.0 * cm]))

    flow.append(Paragraph("Findings (long-document regime) — conservative", ss["H2b"]))
    flow.append(Paragraph(
        "<b>1. At long context, budget-matched retrieval COLLAPSES; DESi holds at ~2% of the tokens.</b> "
        "B = 1.0 (Sonnet) / 0.96 (Granite) on ~372 input tokens; full chat A = 0.88 / 0.76 on ~18,342 "
        "tokens (49× more) and is actually WORSE than B. Budget-matched retrieval at 1% of the chunks: "
        "BM25 ≈ 0.44–0.52, small-neural (bge-small) ≈ 0.08–0.10. So DESi delivers better-than-full-"
        "context recall at ~1/49 the cost — and beats budget retrieval by ~0.5 (BM25) to ~0.9 (neural).", ss["B2"]))
    flow.append(Paragraph(
        "<b>2. This resolves the k-question honestly.</b> The earlier k-sweep showed retrieval can match "
        "DESi on SHORT chats (optimal k ≈ all chunks is cheap). On LONG documents that is impossible: "
        "'all chunks' does not fit the budget, and at 1% the small embedder is fooled by generically-"
        "relevant filler (it retrieves 'Unrelated sidebar… how is X set up' over the actual decision "
        "turns; BM25's keyword match is more robust). DESi's advantage is therefore TOKEN EFFICIENCY + "
        "robustness, and it is LARGE precisely in the long-document regime DESi is meant for.", ss["B2"]))
    flow.append(Paragraph(
        "<b>3. Auto-construction survives long context.</b> B_auto = 0.96 (Sonnet) / 0.88 (Granite): "
        "one extraction pass still finds and resolves the supersession buried in ~990 turns. B−B_auto "
        "= +0.04 / +0.08 (within/near noise). So the live-state slice is auto-constructible even from "
        "long, noisy documents — and a small model (Granite) does it nearly as well.", ss["B2"]))
    flow.append(Paragraph(
        "<b>4. Confidently-wrong tracks retrieval failure.</b> confidence_while_wrong: R2n = 0.6 / 0.2, "
        "R1 = 0.4 / 0.6, while A = B = B_auto = 0. Retrieval confidently reports filler when it misses "
        "the needles; the resolved state removes that failure mode.", ss["B2"]))
    flow.append(Spacer(1, 0.1 * cm))
    flow.append(Paragraph(
        "<b>Caveats.</b> The neural collapse is for a SMALL embedder (bge-small, 384d) with a generic-"
        "task query; a stronger embedder or query expansion would rank needles better — so R2n≈0.08 is "
        "a weak-retrieval floor, and B−R1≈+0.5 is the more representative gap. N=5, 2 reps → directional. "
        "B's slice is curated, but B_auto shows it is constructible. The filler is synthetic distractor.", ss["Sm"]))
    flow.append(Paragraph(
        "<b>Net across short+long:</b> DESi's value over retrieval is (i) TOKEN EFFICIENCY — full-"
        "context-or-better recall at ~2% of the tokens — and (ii) ROBUSTNESS on long documents where "
        "budget retrieval cannot fit / find the needles; both are auto-constructible. It is NOT a "
        "large absolute-capability win at unlimited budget (short-doc k-sweep), and metadata governance "
        "stays unestablished. No 'smarter' / 'wins generally' claim. Cost: ~130 calls.", ss["B2"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4), title="DESi ablation Phase-5",
                      leftMargin=1.2 * cm, rightMargin=1.2 * cm, topMargin=1.1 * cm,
                      bottomMargin=1.1 * cm).build(flow)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

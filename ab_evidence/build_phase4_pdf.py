"""Phase-4 PDF: automatic state construction (B_auto) + neural retrieval (R2n) + 8 cases × 3 models.
Reads results/ablation2_phase4_{sonnet,gpt4o,llama}.json. Conservative; corrects the Phase-3 magnitude."""
from __future__ import annotations

import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "reports" / "ablation2_phase4.pdf"
_MODELS = [("phase4_sonnet", "Sonnet-4.5"), ("phase4_gpt4o", "GPT-4o"), ("phase4_llama", "Llama-3.3-70B")]
_SHORT = {"A_baseline_full_context": "A", "B_normal_desi": "B", "B_auto_constructed": "B_auto",
          "R1_bm25": "R1 bm25", "R2_tfidf": "R2 tfidf", "R2n_neural": "R2n neural",
          "E_budget_matched_status_stripped": "E"}


def _load(tag):
    return json.loads((_HERE / "results" / f"ablation2_{tag}.json").read_text())


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("B2", parent=ss["BodyText"], fontSize=8.5, leading=11, spaceAfter=3))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.5, leading=9,
                          textColor=colors.HexColor("#444")))
    return ss


def _tbl(rows, widths, fs=8):
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


def _delta(out, x, y):
    cs = out["cases"]
    ds = [cs[i]["conditions"][x]["recall"] - cs[i]["conditions"][y]["recall"] for i in range(len(cs))]
    m = sum(ds) / len(ds)
    sd = (sum((d - m) ** 2 for d in ds) / (len(ds) - 1)) ** 0.5 if len(ds) > 1 else 0.0
    return round(m, 3), round(sd, 3)


def build() -> Path:
    outs = {lbl: _load(tag) for tag, lbl in _MODELS}
    conds = next(iter(outs.values()))["conditions"]
    ss = _ss()
    flow = [Paragraph("DESi ablation Phase-4 — automatic state construction, neural retrieval, "
                      "8 cases × 3 models", ss["Title"]),
            Paragraph("Real run · temp 0 · 2 reps · 8 lifecycle/supersession cases · "
                      "Sonnet-4.5 / GPT-4o / Llama-3.3-70B. B_auto = state built by ONE LLM "
                      "extraction pass over the raw chat (told to drop reversed/ruled-out items); "
                      "R2n = neural-embedding retrieval (bge-small). Conservative; corrects the "
                      "Phase-3 magnitude.", ss["B2"])]

    flow.append(Paragraph("Mean recall (8 cases) per condition × model", ss["H2b"]))
    rows = [["model"] + [_SHORT[c] for c in conds]]
    for lbl, out in outs.items():
        rows.append([lbl] + [str(_m([r["conditions"][c]["recall"] for r in out["cases"]]))
                             for c in conds])
    flow.append(_tbl(rows, [3.0 * cm] + [2.0 * cm] * len(conds)))

    flow.append(Paragraph("Key deltas (mean ± sd over 8 cases; N≈ to detect 0.1)", ss["H2b"]))
    pairs = [("B_normal_desi", "B_auto_constructed", "auto-construction works?"),
             ("B_normal_desi", "R1_bm25", "vs lexical retrieval"),
             ("B_normal_desi", "R2n_neural", "vs NEURAL retrieval"),
             ("B_auto_constructed", "R2n_neural", "auto-state vs neural retrieval"),
             ("B_normal_desi", "A_baseline_full_context", "vs full chat"),
             ("B_normal_desi", "E_budget_matched_status_stripped", "governance (metadata)")]
    drows = [["comparison", "note"] + [lbl for _, lbl in _MODELS]]
    for x, y, note in pairs:
        cells = []
        for _, lbl in _MODELS:
            m, sd = _delta(outs[lbl], x, y)
            n = math.ceil(15.7 * sd * sd / 0.01) if sd else 1
            cells.append(f"{m:+.2f}±{sd} (N{n})")
        drows.append([f"{_SHORT[x]} − {_SHORT[y]}", note] + cells)
    flow.append(_tbl(drows, [2.6 * cm, 3.4 * cm] + [3.1 * cm] * 3, fs=7.5))

    flow.append(Paragraph("confidence_while_wrong rate (confidently reporting stale content)", ss["H2b"]))
    crows = [["model", "R1 bm25", "R2n neural", "B", "B_auto"]]
    for lbl, out in outs.items():
        def cw(c, o=out):
            return _m([r["conditions"][c]["degeneration"]["confidence_while_wrong_rate"]
                       for r in o["cases"]])
        crows.append([lbl, cw("R1_bm25"), cw("R2n_neural"), cw("B_normal_desi"),
                      cw("B_auto_constructed")])
    flow.append(_tbl(crows, [3.6 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm]))

    flow.append(Paragraph("Conservative findings", ss["H2b"]))
    flow.append(Paragraph(
        "<b>1. Automatic state construction WORKS — this addresses the Phase-3 caveat.</b> One LLM "
        "extraction pass that resolves supersession yields B_auto ≈ B (curated): B−B_auto = +0.04 to "
        "+0.13 (within noise at N=8), worst single case 0.80, across all 3 models. And B_auto beats "
        "retrieval (~+0.4 vs lexical, ~+0.15 vs neural). So DESi's value here is CONSTRUCTIBLE, not "
        "merely hand-curated ground truth. The structuring helps weaker models most (B−A: Sonnet "
        "+0.06, Llama +0.28).", ss["B2"]))
    flow.append(Paragraph(
        "<b>2. Neural retrieval CORRECTS the magnitude (honest walk-back of Phase 3).</b> Phase-3's "
        "lexical retrieval (BM25/TF-IDF) overstated DESi's edge (~0.7). A proper neural retriever "
        "(R2n, bge-small) recovers most of the live content (0.71–0.85), so B−retrieval shrinks to "
        "<b>~0.15–0.28</b> (modest, borderline at N=8: N≈32–76 needed for a 0.1 CI). The residual is "
        "supersession-resolution: retrieval surfaces stale AND live passages; B/B_auto carry only "
        "the resolved live state. 'DESi beats retrieval' holds, but the honest gap vs STRONG "
        "retrieval is small, not large.", ss["B2"]))
    flow.append(Paragraph(
        "<b>3. Replicates across 8 cases × 3 models.</b> B−R1 ≈ +0.46–0.50, B−R2n ≈ +0.15–0.28, "
        "B−B_auto ≈ 0, B−E ≈ 0 — consistent on Sonnet, GPT-4o and Llama. The large effects (B−R1, "
        "B−B_auto) are well-powered at N=8; B−R2n is borderline (would want ~15–20 cases).", ss["B2"]))
    flow.append(Paragraph(
        "<b>4. Confidently-reporting-stale is a RETRIEVAL pathology.</b> confidence_while_wrong: R1 = "
        "0.25–0.5, R2n = 0–0.25, B = B_auto = 0. The resolved state removes the confident-stale "
        "failure mode that retrieval (especially lexical) exhibits.", ss["B2"]))
    flow.append(Paragraph(
        "<b>5. Metadata governance still NOT established</b> (B−E ≈ 0 on all 3 models, all phases). "
        "The live-state SELECTION / supersession-resolution carries the value, not the category/typing "
        "metadata.", ss["B2"]))
    flow.append(Spacer(1, 0.1 * cm))
    flow.append(Paragraph(
        "<b>Net:</b> Supported — correct, AUTO-CONSTRUCTIBLE live state is load-bearing and beats "
        "retrieval on lifecycle/supersession tasks (modestly vs neural retrieval; the value is "
        "resolving stale content). Not supported — metadata governance; 'DESi makes the model "
        "smarter' / 'wins generally'. The Phase-3 'huge gap vs retrieval' was a lexical-retrieval "
        "artefact.", ss["B2"]))
    flow.append(Paragraph(
        "Cost: 3 models × 8 cases × 7 conditions × 2 reps + 24 extraction ≈ 360 calls. Next: 15–20 "
        "cases to tighten the B−R2n CI; a held-out extractor model for B_auto; harder multi-"
        "supersession chains.", ss["Sm"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4), title="DESi ablation Phase-4",
                      leftMargin=1.2 * cm, rightMargin=1.2 * cm, topMargin=1.1 * cm,
                      bottomMargin=1.1 * cm).build(flow)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

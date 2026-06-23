"""Render the A/B/C/D ablation result into a single PDF (reportlab, like build_pdf.py).

Reads results/ablation_{core,density}.json and writes reports/ablation_results.pdf. Deterministic;
honest about the UNAVAILABLE backend. No new dependency beyond reportlab (already used in the repo).
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_HERE = Path(__file__).resolve().parent
_RES = _HERE / "results"
_OUT = _HERE / "reports" / "ablation_results.pdf"

_COND_DESC = {
    "A_baseline_full_context": "A — baseline: the full chat history.",
    "B_normal_desi": "B — normal DESi: the case's own categorised state slice (id+what per category).",
    "C_wrong_slice": "C — wrong-slice: B's format/budget, but another case's state (cross-domain donor).",
    "D_status_stripped": "D — status-stripped: B's claim texts with governance metadata removed.",
    "E_budget_matched_status_stripped": ("E — budget-matched status-stripped: D's texts, no metadata, "
                                         "padded with inert filler to B's token budget (~1%)."),
}


def _load(tag: str) -> dict | None:
    p = _RES / f"ablation_{tag}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Body2", parent=ss["BodyText"], fontSize=9, leading=12,
                          spaceAfter=4))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=12, spaceBefore=10,
                          spaceAfter=4))
    ss.add(ParagraphStyle("Small", parent=ss["BodyText"], fontSize=8, leading=10,
                          textColor=colors.HexColor("#444444")))
    return ss


def _input_table(out: dict) -> Table:
    head = ["case", "condition", "input_tokens", "slice_info_recall"]
    rows = [head]
    for case in out["cases"]:
        cid = case["case_id"].replace("_padded", "").replace("_long_research", "")
        for cond in out["conditions"]:
            r = case["conditions"][cond]
            rows.append([cid, cond.split("_")[0], str(r["input_token_estimate"]),
                         "-" if r["slice_info_recall"] is None else str(r["slice_info_recall"])])
    t = Table(rows, repeatRows=1, colWidths=[3.2 * cm, 2.2 * cm, 3.0 * cm, 4.0 * cm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    # highlight the C (wrong-slice) info-recall cells = 0.0 and B/D = 1.0
    for i, row in enumerate(rows[1:], start=1):
        if row[1] == "C":
            style.append(("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#b00020")))
            style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
        elif row[1] in ("B", "D"):
            style.append(("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#0a7d2c")))
    t.setStyle(TableStyle(style))
    return t


def build() -> Path:
    core = _load("core")
    density = _load("density")
    if core is None:
        raise SystemExit("run `python ab_evidence/ablation_run.py` first")
    ss = _styles()
    backend = core["backend_status"]
    flow = []
    flow.append(Paragraph("DESi ablation — is the gain selection, governance, or just "
                          "structured context?", ss["Title"]))
    flow.append(Paragraph("Falsification-oriented extension of the ab_evidence A/B harness. "
                          "This reports the <b>instrument and the deterministic input-side "
                          "result</b>; it is not an empirical verdict on DESi.", ss["Body2"]))
    flow.append(Paragraph(f"Backend status: <b>{backend}</b>. "
                          + ("Model-dependent accuracy &amp; degeneration are measured."
                             if backend == "REAL" else
                             "No API key in this environment, so accuracy &amp; degeneration are "
                             "<b>UNAVAILABLE</b> and <b>not simulated</b> (per the harness's "
                             "no-mock discipline)."), ss["Body2"]))

    flow.append(Paragraph("Conditions", ss["H2b"]))
    for cond in core["conditions"]:
        flow.append(Paragraph("• " + _COND_DESC[cond].replace("—", "&mdash;"), ss["Body2"]))

    flow.append(Paragraph("Input-side characterisation (deterministic, no model)", ss["H2b"]))
    flow.append(Paragraph("<i>slice_info_recall</i> = fraction of the case's true ground-truth "
                          "items actually inside the injected slice. It shows the wrong slice (C) "
                          "really starves the model of correct information "
                          "(<font color='#b00020'>0.0</font>) while B and D carry it "
                          "(<font color='#0a7d2c'>1.0</font>); A has the full chat. This describes "
                          "the <b>inputs</b>, not model behaviour.", ss["Body2"]))
    flow.append(Paragraph("Core cases", ss["Small"]))
    flow.append(_input_table(core))
    flow.append(Spacer(1, 0.3 * cm))
    flow.append(Paragraph("Density sweep (padding grows A; slice constant)", ss["Small"]))
    if density:
        flow.append(_input_table(density))
    flow.append(Paragraph("Note: D is ~35&ndash;40% smaller than B (that gap IS the governance "
                          "metadata's footprint). <b>E</b> controls for it &mdash; D's texts padded "
                          "with inert filler to B's budget (within ~1%) &mdash; so only <b>B&gt;E</b> "
                          "(not merely B&gt;D) would be evidence for the metadata. Runner: temp 0, "
                          "fixed seed, 3 reps/case.", ss["Small"]))

    flow.append(Paragraph("Degeneration metrics (first-class, deterministic, unit-tested)",
                          ss["H2b"]))
    for name, what in [
        ("loop_trap", "the answer repeats near-identical units (stuck in a loop)"),
        ("contradiction_persistence", "a known open conflict restated as if settled"),
        ("invalid_claim_reuse", "the answer restates a claim from a known-invalid pool"),
        ("bad_framing_nonrecovery", "share of the answer traceable to a wrong injected slice"),
        ("coherence_without_continuity", "fluent output that preserves little of the true state"),
    ]:
        flow.append(Paragraph(f"• <b>{name}</b> — {what}", ss["Body2"]))

    flow.append(Paragraph("What would weaken vs strengthen the DESi claim", ss["H2b"]))
    flow.append(Paragraph("<b>Weaken:</b> C ≈ B on accuracy (gain is generic structured context); "
                          "D ≈ B (metadata decorative); A ≥ B except at extreme density "
                          "(long-context artefact).", ss["Body2"]))
    flow.append(Paragraph("<b>Strengthen:</b> C collapses / high bad_framing_nonrecovery "
                          "(selection is load-bearing); <b>B &gt; E</b> (budget-matched) on "
                          "conflict/decision typing and degeneration (metadata governs, not token "
                          "count); B's edge and lower degeneration grow with density (robustness "
                          "under pressure).", ss["Body2"]))

    flow.append(Paragraph("Limitations (stated plainly)", ss["H2b"]))
    flow.append(Paragraph("No backend here (instrument only, no verdict). Tiny sample "
                          f"({len(core['cases'])} core + {len(density['cases']) if density else 0} "
                          "density) &mdash; no significance. D token-budget confound now controlled "
                          "by E. Paraphrase-blind evaluator (relative comparison only). Wrong-slice "
                          "budget only approximate. Negative results are primary; no promotional "
                          "claims.", ss["Body2"]))
    flow.append(Paragraph("Reproduce: <font face='Courier'>python ab_evidence/ablation_run.py</font>"
                          " (deterministic) &middot; set OPENROUTER_API_KEY then re-run for the full "
                          "table &middot; <font face='Courier'>pytest tests/ab_ablation -q</font>.",
                          ss["Small"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=A4, title="DESi ablation results",
                      leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                      topMargin=1.4 * cm, bottomMargin=1.4 * cm).build(flow)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

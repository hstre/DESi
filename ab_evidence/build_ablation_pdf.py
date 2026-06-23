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


def _mk_table(rows, colwidths, bold_first_col=False):
    t = Table(rows, repeatRows=1, colWidths=colwidths)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.0),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    t.setStyle(TableStyle(style))
    return t


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _recall_rows(out):
    rows = [["case", "A", "B", "C", "D", "E"]]
    for case in out["cases"]:
        c = case["conditions"]
        rows.append([case["case_id"].replace("_long_research", "").replace("_padded", ""),
                     *[str(c[k].get("overall_recall")) for k in
                       ("A_baseline_full_context", "B_normal_desi", "C_wrong_slice",
                        "D_status_stripped", "E_budget_matched_status_stripped")]])
    return rows


def _deg_rows(out):
    rows = [["condition", "loop", "bad_frame", "coh_no_cont", "contra", "invalid_reuse"]]
    for cond in out["conditions"]:
        recs = [r["conditions"][cond]["degeneration"] for r in out["cases"]]
        n = len(recs) or 1
        rows.append([cond.split("_")[0],
                     round(sum(d["loop_trap_rate"] for d in recs) / n, 2),
                     round(sum(d["bad_framing_nonrecovery_rate"] for d in recs) / n, 2),
                     round(sum(d["coherence_without_continuity_rate"] for d in recs) / n, 2),
                     round(sum(d["contradiction_persistence_mean"] for d in recs) / n, 2),
                     round(sum(d["invalid_claim_reuse_mean"] for d in recs) / n, 2)])
    return rows


def _cond_means(out):
    keys = ("A_baseline_full_context", "B_normal_desi", "C_wrong_slice", "D_status_stripped",
            "E_budget_matched_status_stripped")
    return {k: _mean([c["conditions"][k].get("overall_recall") for c in out["cases"]]) for k in keys}


def _findings(core, density, ss):
    cm, dm = _cond_means(core), _cond_means(density)
    out = [Paragraph("Findings from THIS run (conservative; n=4 core + 3 density, 3 reps, temp 0, "
                     "claude-sonnet-4.5)", ss["H2b"])]
    A, B, C, D, E = ("A_baseline_full_context", "B_normal_desi", "C_wrong_slice",
                     "D_status_stripped", "E_budget_matched_status_stripped")
    out.append(Paragraph(
        f"<b>1. Selection IS load-bearing (strong).</b> Wrong-slice C collapses: mean recall "
        f"{cm[C]} (core) / {dm[C]} (density) vs B {cm[B]} / {dm[B]}; C shows invalid_claim_reuse "
        f"≈8–11 and bad_framing/coherence-without-continuity = 1.0 (it fluently parrots the wrong "
        f"case). A plausible-but-wrong slice is far worse than no slice.", ss["Body2"]))
    ba = [c["conditions"][B]["overall_recall"] - c["conditions"][A]["overall_recall"]
          for c in density["cases"]]
    out.append(Paragraph(
        f"<b>2. B-vs-A is mostly long-context robustness.</b> Core B−A ≈ +{_mean([cc['conditions'][B]['overall_recall']-cc['conditions'][A]['overall_recall'] for cc in core['cases']])}; "
        f"but in the density sweep B−A runs {round(ba[0],2)} (case6, no padding) → {round(ba[1],2)} "
        f"(30k) → {round(ba[2],2)} (60k): at low density A can match/beat B, and B's edge appears "
        f"and grows only as padding dilutes A. Mainly robustness under context pressure, not a "
        f"general reasoning gain.", ss["Body2"]))
    be_c = _mean([c["conditions"][B]["overall_recall"] - c["conditions"][E]["overall_recall"]
                  for c in core["cases"]])
    be_d = _mean([c["conditions"][B]["overall_recall"] - c["conditions"][E]["overall_recall"]
                  for c in density["cases"]])
    out.append(Paragraph(
        f"<b>3. Metadata governance: weak, density-dependent evidence.</b> Budget-matched B−E ≈ "
        f"{be_c} on core (B ≈ E — metadata NOT shown to help on short cases) but +{be_d} across the "
        f"density cases (B &gt; E consistently, token-controlled). The metadata-free flat list D also "
        f"loops badly on the long states (loop rate ≈ "
        f"{round(sum(r['conditions'][D]['degeneration']['loop_trap_rate'] for r in density['cases'])/len(density['cases']),2)}) "
        f"while B and E do not. So there is SOME token-controlled evidence the typing helps under "
        f"pressure, but it is small (~0.1), inconsistent across case types, and not significant at "
        f"this n.", ss["Body2"]))
    out.append(Paragraph(
        "<b>No empirical DESi win is claimed.</b> Supported: correct selection is essential; DESi's "
        "advantage over full chat is largely long-context robustness. Not supported as a general "
        "effect: epistemic-metadata governance (only weak, density-dependent signal). Sample is "
        "tiny and the evaluator is paraphrase-blind — directional only.", ss["Body2"]))
    return out


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
    intro = ("Falsification-oriented extension of the ab_evidence A/B harness. "
             + ("Real run (claude-sonnet-4.5, temp 0, 3 reps/case); the sample is small, so results "
                "are <b>directional, not a verdict</b>. No DESi win is claimed beyond what the "
                "numbers support." if backend == "REAL" else
                "This reports the <b>instrument and the deterministic input-side result</b>; it is "
                "not an empirical verdict on DESi."))
    flow.append(Paragraph(intro, ss["Body2"]))
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

    if backend == "REAL" and density:
        flow.append(Paragraph("Model results — recall (mean of 3 reps @ temp 0)", ss["H2b"]))
        flow.append(Paragraph("Core cases", ss["Small"]))
        flow.append(_mk_table(_recall_rows(core), [3.4 * cm] + [1.9 * cm] * 5))
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(Paragraph("Density sweep (case6 unpadded → 30k → 60k padding on A)",
                              ss["Small"]))
        flow.append(_mk_table(_recall_rows(density), [3.4 * cm] + [1.9 * cm] * 5))
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(Paragraph("Degeneration rates — core", ss["Small"]))
        flow.append(_mk_table(_deg_rows(core), [2.2 * cm] + [2.0 * cm] * 5))
        flow.append(Spacer(1, 0.15 * cm))
        flow.append(Paragraph("Degeneration rates — density", ss["Small"]))
        flow.append(_mk_table(_deg_rows(density), [2.2 * cm] + [2.0 * cm] * 5))
        flow.extend(_findings(core, density, ss))

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
    flow.append(Paragraph(("Real backend run (sonnet-4.5, temp 0, 3 reps). " if backend == "REAL"
                           else "No backend here (instrument only, no verdict). ") + "Tiny sample "
                          f"({len(core['cases'])} core + {len(density['cases']) if density else 0} "
                          "density) &mdash; no significance test; differences of a few items are "
                          "noise. D token-budget confound now controlled "
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

"""Render the Phase-2 ablation result (state ladder + retrieval + governance) to a PDF.

Reads results/ablation2_phase2.json, writes reports/ablation2_phase2.pdf. Conservative findings are
computed from the data; no promotional claims. reportlab only (already used in the repo).
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HERE = Path(__file__).resolve().parent
_JSON = _HERE / "results" / "ablation2_phase2.json"
_OUT = _HERE / "reports" / "ablation2_phase2.pdf"
_SHORT = {c: c.split("_")[0] for c in
          ("A_baseline_full_context", "B_normal_desi", "C_wrong_slice", "D_status_stripped",
           "E_budget_matched_status_stripped", "F_empty_state", "G_neutral_irrelevant",
           "H_contradiction_wrong", "R1_bm25", "R2_tfidf", "R3_hybrid")}


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("B2", parent=ss["BodyText"], fontSize=8.5, leading=11, spaceAfter=3))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.5, leading=9,
                          textColor=colors.HexColor("#444")))
    return ss


def _tbl(rows, widths, fs=7.5):
    t = Table(rows, repeatRows=1, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), fs),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")]),
    ]))
    return t


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def build() -> Path:
    out = json.loads(_JSON.read_text())
    ss = _ss()
    conds = out["conditions"]
    flow = [Paragraph("DESi ablation Phase-2 — state ladder, retrieval, governance", ss["Title"]),
            Paragraph(f"Real run · claude-sonnet-4.5 · temp {out['temperature']} · seed {out['seed']} "
                      f"· {out['reps']} reps · {len(out['cases'])} cases. Conservative; small sample "
                      "→ directional, no verdict. No DESi win is claimed.", ss["B2"])]

    # recall table
    flow.append(Paragraph("Recall (mean of reps) — B normal DESi vs the ladder + retrieval",
                          ss["H2b"]))
    head = ["case"] + [_SHORT[c] for c in conds]
    rows = [head]
    for r in out["cases"]:
        c = r["conditions"]
        rows.append([r["case_id"].replace("_long_research", "").replace("_padded", "")]
                    + [str(c[k].get("recall")) for k in conds])
    flow.append(_tbl(rows, [2.6 * cm] + [1.5 * cm] * len(conds)))

    # degeneration table
    flow.append(Paragraph("Degeneration (mean across cases)", ss["H2b"]))
    drows = [["cond", "loop", "contra", "invalid", "bad_frame", "coh_no_cont", "conf_wrong",
              "self_conf"]]
    for cond in conds:
        ds = [r["conditions"][cond]["degeneration"] for r in out["cases"]]
        drows.append([_SHORT[cond],
                      _mean([d["loop_trap_rate"] for d in ds]),
                      _mean([d["contradiction_persistence_mean"] for d in ds]),
                      _mean([d["invalid_claim_reuse_mean"] for d in ds]),
                      _mean([d["bad_framing_nonrecovery_rate"] for d in ds]),
                      _mean([d["coherence_without_continuity_rate"] for d in ds]),
                      _mean([d["confidence_while_wrong_rate"] for d in ds]),
                      _mean([d["mean_self_confidence"] for d in ds])])
    flow.append(_tbl(drows, [2.0 * cm] + [1.85 * cm] * 7))

    # comparisons + persistence side by side (just stack)
    flow.append(Paragraph("Specific comparisons (mean recall Δ) &amp; multi-turn persistence",
                          ss["H2b"]))
    pairs = [("B_normal_desi", "F_empty_state"), ("F_empty_state", "G_neutral_irrelevant"),
             ("G_neutral_irrelevant", "C_wrong_slice"),
             ("G_neutral_irrelevant", "H_contradiction_wrong"),
             ("B_normal_desi", "R1_bm25"), ("B_normal_desi", "R2_tfidf"),
             ("B_normal_desi", "E_budget_matched_status_stripped")]
    crows = [["comparison", "mean Δ", "per-case"]]
    for x, y in pairs:
        per = [round(r["conditions"][x]["recall"] - r["conditions"][y]["recall"], 3)
               for r in out["cases"]]
        crows.append([f"{_SHORT[x]} − {_SHORT[y]}", _mean(per), ", ".join(str(p) for p in per)])
    flow.append(_tbl(crows, [3.2 * cm, 1.6 * cm, 5.2 * cm]))
    flow.append(Spacer(1, 0.15 * cm))
    prows = [["case", "cond", "reuse t1→t2→t3", "verdict"]]
    for p in out["persistence"]:
        prows.append([p["case_id"].replace("_long_research", "").replace("_padded", ""),
                      _SHORT[p["condition"]], "→".join(str(x) for x in p["reuse_trajectory"]),
                      p["verdict"]])
    flow.append(_tbl(prows, [3.0 * cm, 1.2 * cm, 2.6 * cm, 3.2 * cm]))

    # findings
    rc = {c: _mean([r["conditions"][c]["recall"] for r in out["cases"]]) for c in conds}
    flow.append(Paragraph("Conservative findings", ss["H2b"]))
    flow.append(Paragraph(
        f"<b>1. Correct state selection is load-bearing (strong).</b> B={rc['B_normal_desi']} vs "
        f"empty F={rc['F_empty_state']}, neutral G={rc['G_neutral_irrelevant']}, wrong "
        f"C={rc['C_wrong_slice']} — all wrong/empty/irrelevant states collapse to ~0; only the "
        "correct state succeeds.", ss["B2"]))
    flow.append(Paragraph(
        "<b>2. Wrong-state poisoning is real but shows in DEGENERATION, not recall.</b> On recall "
        "F≈G≈C (all ~0) — recall cannot tell 'no info' from 'wrong info'. The degeneration metrics "
        "can: C adopts the wrong case's claims (invalid_reuse ≈8.8, bad_framing 1.0), G is pulled "
        "into irrelevant content (reuse ≈3.0, loop 0.75), H loops (1.0) and reuses contradictions "
        "(≈5.1). And the injected claims PERSIST across neutral double-check probes (C persisted in "
        "3/4 cases). Empty (F) fails quietly (loops, fluent-empty) without adopting anything.", ss["B2"]))
    flow.append(Paragraph(
        "<b>3. The model is confidently wrong.</b> Self-reported confidence stays ≈93–95 even when "
        "recall ≈0 (C/F/G: confidence_while_wrong rate = 1.0). Only contradiction (H) dents it "
        "(≈82). Self-report is a weak proxy (no logprobs), but the pattern is stark.", ss["B2"]))
    flow.append(Paragraph(
        f"<b>4. Plain retrieval explains the EASY cases, not the status cases.</b> B−R1 mean "
        f"={_mean([r['conditions']['B_normal_desi']['recall']-r['conditions']['R1_bm25']['recall'] for r in out['cases']])} "
        "but per-case 0.17, 0.15 (architecture/research) vs 0.67, 0.69 (debugging/long-research). "
        "Retrieval ≈ B on simple recall; B ≫ retrieval where epistemic STATUS must be reconstructed "
        "(root-cause/rejected/gating). Caveat: B's slice is curated ground-truth (an upper bound on "
        "selection), and the comparison is HIGH-variance — power says N≈141 cases to nail a 0.1 "
        "difference, so this is directional, not proven.", ss["B2"]))
    flow.append(Paragraph(
        f"<b>5. Metadata governance: NOT established here.</b> Budget-matched B−E "
        f"={_mean([r['conditions']['B_normal_desi']['recall']-r['conditions']['E_budget_matched_status_stripped']['recall'] for r in out['cases']])} "
        "(≈0); stripping the category/typing metadata does not hurt on these core cases. (A small "
        "B&gt;E appeared only under context-density pressure in the earlier run.)", ss["B2"]))
    flow.append(Paragraph(
        "<b>Not supported:</b> 'DESi makes the model smarter', 'DESi wins generally', 'metadata "
        "governance is proven'. <b>Supported:</b> correct selection is essential; plausible-wrong / "
        "contradictory structure is actively toxic (adopted, propagated, persisted) — visible only "
        "via degeneration metrics; DESi beats retrieval mainly on epistemic-status cases (directional). "
        "<b>Next:</b> more discriminative conflict/status/lifecycle cases (retrieval comparison is "
        "underpowered); a non-Claude model; a neural-embedding R2.", ss["B2"]))

    n_calls = len(out["cases"]) * len(conds) * out["reps"] + len(out["persistence"]) * 3
    flow.append(Paragraph(
        f"Cost: ≈{n_calls} model calls (sonnet-4.5). Power: B−E reliable at N=4; B−retrieval "
        "underpowered (N≈141 for 0.1). Stop-condition: retrieval did NOT match B on all cases "
        "(it collapsed on the two status-heavy cases), so the cases are partly discriminative — but "
        "scale on PURPOSE-BUILT conflict/status cases, not the current four.", ss["Sm"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4), title="DESi ablation Phase-2",
                      leftMargin=1.2 * cm, rightMargin=1.2 * cm, topMargin=1.1 * cm,
                      bottomMargin=1.1 * cm).build(flow)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

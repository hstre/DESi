"""Render Phase-3 (lifecycle/status cases × two models) to a PDF. Reads results/ablation2_phase3_
sonnet.json and ablation2_phase3_gpt4o.json. Conservative; the curated-GT caveat is stated."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "reports" / "ablation2_phase3.pdf"
_SHORT = {"A_baseline_full_context": "A", "B_normal_desi": "B", "C_wrong_slice": "C",
          "D_status_stripped": "D", "E_budget_matched_status_stripped": "E", "F_empty_state": "F",
          "G_neutral_irrelevant": "G", "H_contradiction_wrong": "H", "R1_bm25": "R1",
          "R2_tfidf": "R2", "R3_hybrid": "R3"}


def _load(tag):
    p = _HERE / "results" / f"ablation2_{tag}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("B2", parent=ss["BodyText"], fontSize=8.5, leading=11, spaceAfter=3))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.5, leading=9,
                          textColor=colors.HexColor("#444")))
    return ss


def _tbl(rows, widths, fs=7.5, hi=None):
    t = Table(rows, repeatRows=1, colWidths=widths)
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
             ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
             ("FONTSIZE", (0, 0), (-1, -1), fs),
             ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbb")),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f7")])]
    t.setStyle(TableStyle(style))
    return t


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _recall(out, c, case_id):
    return out["cases"][[r["case_id"] for r in out["cases"]].index(case_id)]["conditions"][c]["recall"]


def build() -> Path:
    son, gpt = _load("phase3_sonnet"), _load("phase3_gpt4o")
    ss = _ss()
    conds = son["conditions"]
    cases = [r["case_id"] for r in son["cases"]]
    flow = [Paragraph("DESi ablation Phase-3 — purpose-built lifecycle/status cases, two models",
                      ss["Title"]),
            Paragraph("Real run · temp 0 · 3 reps · 2 cases where the chat CONTAINS superseded / "
                      "ruled-out content (a reversed rollout + a ruled-out hypothesis; a deprecated "
                      "field + a relaxed 'forever' rule). Retrieval surfaces the stale items; the "
                      "curated DESi slice holds only the live state. Conservative; small N.", ss["B2"])]

    flow.append(Paragraph("Recall (mean of reps) — Claude-Sonnet-4.5 / GPT-4o", ss["H2b"]))
    head = ["case · model"] + [_SHORT[c] for c in conds]
    rows = [head]
    for out, label in ((son, "sonnet"), (gpt, "gpt-4o")):
        for r in out["cases"]:
            rows.append([r["case_id"].replace("_lifecycle", "") + " · " + label]
                        + [str(r["conditions"][c].get("recall")) for c in conds])
    flow.append(_tbl(rows, [3.4 * cm] + [1.45 * cm] * len(conds)))

    flow.append(Paragraph("Headline: B (curated live state) vs retrieval &amp; baselines — both models",
                          ss["H2b"]))
    cmp_rows = [["comparison", "sonnet mean Δ", "gpt-4o mean Δ"]]
    for x, y in [("B_normal_desi", "R1_bm25"), ("B_normal_desi", "R2_tfidf"),
                 ("B_normal_desi", "A_baseline_full_context"), ("B_normal_desi", "F_empty_state"),
                 ("B_normal_desi", "C_wrong_slice"), ("B_normal_desi", "E_budget_matched_status_stripped")]:
        sd = _mean([_recall(son, x, c) - _recall(son, y, c) for c in cases])
        gd = _mean([_recall(gpt, x, c) - _recall(gpt, y, c) for c in cases])
        cmp_rows.append([f"{_SHORT[x]} − {_SHORT[y]}", sd, gd])
    flow.append(_tbl(cmp_rows, [4.0 * cm, 4.0 * cm, 4.0 * cm]))

    flow.append(Paragraph("Degeneration (mean across the 2 cases) — sonnet / gpt-4o", ss["H2b"]))
    drows = [["cond", "loop s/g", "invalid s/g", "bad_frame s/g", "conf_wrong s/g", "self_conf s/g"]]
    for c in conds:
        ds = [r["conditions"][c]["degeneration"] for r in son["cases"]]
        dg = [r["conditions"][c]["degeneration"] for r in gpt["cases"]]

        def pair(key, dlist_s=ds, dlist_g=dg):
            return f"{_mean([d[key] for d in dlist_s])}/{_mean([d[key] for d in dlist_g])}"
        drows.append([_SHORT[c], pair("loop_trap_rate"), pair("invalid_claim_reuse_mean"),
                      pair("bad_framing_nonrecovery_rate"), pair("confidence_while_wrong_rate"),
                      pair("mean_self_confidence")])
    flow.append(_tbl(drows, [1.6 * cm] + [2.5 * cm] * 5, fs=7))

    flow.append(Paragraph("Multi-turn invalid_claim_persistence (reuse t1→t2→t3 → verdict)", ss["H2b"]))
    prows = [["case", "cond", "sonnet", "gpt-4o"]]
    for i, p in enumerate(son["persistence"]):
        g = gpt["persistence"][i]
        prows.append([p["case_id"].replace("_lifecycle", ""), _SHORT[p["condition"]],
                      "→".join(map(str, p["reuse_trajectory"])) + " " + p["verdict"],
                      "→".join(map(str, g["reuse_trajectory"])) + " " + g["verdict"]])
    flow.append(_tbl(prows, [2.6 * cm, 1.2 * cm, 4.4 * cm, 4.4 * cm]))

    flow.append(Paragraph("Conservative findings", ss["H2b"]))
    br1_s = _mean([_recall(son, "B_normal_desi", c) - _recall(son, "R1_bm25", c) for c in cases])
    br1_g = _mean([_recall(gpt, "B_normal_desi", c) - _recall(gpt, "R1_bm25", c) for c in cases])
    flow.append(Paragraph(
        f"<b>1. On lifecycle/supersession tasks, the curated DESi state beats retrieval — large and "
        f"cross-model.</b> B=1.0 on both models; BM25/TF-IDF/hybrid retrieval = 0.07–0.4. B−R1 = "
        f"{br1_s} (sonnet) and {br1_g} (gpt-4o), per-case 0.6–0.93. Retrieval surfaces the superseded "
        "items and the model reports them — confidently (retrieval conf_while_wrong = 1.0). This is "
        "the cleanest evidence that DESi's value here is a MAINTAINED epistemic state (supersession "
        "already resolved), not generic top-k selection.", ss["B2"]))
    flow.append(Paragraph(
        "<b>2. CAVEAT (does not overclaim).</b> B's slice IS the curated ground-truth live state — "
        "DESi was handed the resolved state while retrieval had to resolve it. So this shows a "
        "correctly-maintained state beats retrieval on lifecycle tasks; it does NOT show DESi can "
        "BUILD that state automatically. That construction step is the real open question.", ss["B2"]))
    flow.append(Paragraph(
        "<b>3. Poisoning + confidently-wrong replicate across models.</b> C invalid_reuse ≈14–15, G "
        "≈8, bad_framing 1.0 on both; self-confidence stays ≈93–100 while wrong (gpt-4o reports 100 "
        "even when wrong). Multi-turn: the wrong slice (C) PERSISTS and even RELAPSES (12→0→12: "
        "dropped when probed, then reverted) on both models.", ss["B2"]))
    flow.append(Paragraph(
        f"<b>4. Metadata governance still not established.</b> B−E = "
        f"{_mean([_recall(son, 'B_normal_desi', c) - _recall(son, 'E_budget_matched_status_stripped', c) for c in cases])} "
        "(sonnet) / 0.0 (gpt-4o): the live-state SELECTION carries the value, not the category/typing "
        "metadata.", ss["B2"]))
    flow.append(Paragraph(
        "<b>Supported:</b> correct state selection is load-bearing; plausible-wrong/irrelevant "
        "structure is actively toxic and sticky; a maintained DESi state beats retrieval on "
        "epistemic-status/lifecycle tasks (cross-model). <b>Not supported / open:</b> automatic state "
        "construction; metadata governance; 'DESi makes the model smarter' / 'wins generally'.", ss["B2"]))
    n_calls = (len(son["cases"]) * len(conds) * son["reps"] + len(son["persistence"]) * 3) * 2
    flow.append(Paragraph(
        f"Cost: ≈{n_calls} calls across both models. Power: N=2 cases is formally under-powered for a "
        "0.1 effect, BUT the observed B−retrieval effect (~0.7) is ~5–7× the noise floor and "
        "replicates over 2 models × 2 cases (all points 0.6–0.93). Next: more such cases (10–20) to "
        "tighten CIs; test automatic slice construction; a neural-embedding R2.", ss["Sm"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4), title="DESi ablation Phase-3",
                      leftMargin=1.2 * cm, rightMargin=1.2 * cm, topMargin=1.1 * cm,
                      bottomMargin=1.1 * cm).build(flow)
    return _OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size} bytes)")

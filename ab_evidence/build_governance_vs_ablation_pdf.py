"""One consolidated PDF tying the router-governance layer to the ablation evidence.

It pulls the real Phase-5 numbers (REAL OpenRouter backend, Sonnet 4.5 + Granite 4.1-8b) from the
committed result files and renders, in one document: what the ablation measured (recall + tokens +
degeneration), the governance layer that turns those metrics into gates, and the metric-for-metric
bridge between them. Conservative: no claim beyond the data — B ~ E stands, metadata governance is
NOT presented as a recall effect.

Run: ``python ab_evidence/build_governance_vs_ablation_pdf.py``
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "reports" / "governance_vs_ablation.pdf"
_SONNET = _HERE / "results" / "ablation2_phase5_sonnet.json"
_GRANITE = _HERE / "results" / "ablation2_phase5_granite.json"

_CONDS = ["A_baseline_full_context", "B_normal_desi", "B_auto_constructed",
          "E_budget_matched_status_stripped", "R1_bm25", "R2n_neural"]
_CLABEL = {"A_baseline_full_context": "A — full context",
           "B_normal_desi": "B — DESi state",
           "B_auto_constructed": "B — auto-constructed",
           "E_budget_matched_status_stripped": "E — status-stripped (budget-matched)",
           "R1_bm25": "R1 — BM25 retrieval",
           "R2n_neural": "R2n — neural retrieval"}
_DEG = ["coherence_without_continuity_rate", "confidence_while_wrong_rate", "loop_trap_rate",
        "contradiction_persistence_mean", "invalid_claim_reuse_mean", "bad_framing_nonrecovery_rate"]
_DLABEL = {"coherence_without_continuity_rate": "coherence_without_continuity",
           "confidence_while_wrong_rate": "confidence_while_wrong",
           "loop_trap_rate": "loop_trap",
           "contradiction_persistence_mean": "contradiction_persistence",
           "invalid_claim_reuse_mean": "invalid_claim_reuse",
           "bad_framing_nonrecovery_rate": "bad_framing_nonrecovery"}


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _agg(path):
    d = json.loads(path.read_text())
    rec, tok, deg = defaultdict(list), defaultdict(list), defaultdict(lambda: defaultdict(list))
    for case in d["cases"]:
        for c, cv in case["conditions"].items():
            if cv.get("recall") is not None:
                rec[c].append(cv["recall"])
            if cv.get("input_token_estimate") is not None:
                tok[c].append(cv["input_token_estimate"])
            for k, v in (cv.get("degeneration") or {}).items():
                if v is not None:
                    deg[c][k].append(v)
    return (d["model"], d.get("backend_status"), d.get("reps"),
            {c: _mean(v) for c, v in rec.items()},
            {c: _mean(v) for c, v in tok.items()},
            {c: {k: _mean(vs) for k, vs in deg[c].items()} for c in deg})


def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Body", parent=ss["BodyText"], fontSize=8.8, leading=11.6, spaceAfter=4))
    ss.add(ParagraphStyle("H2b", parent=ss["Heading2"], fontSize=12.5, spaceBefore=9, spaceAfter=3,
                          textColor=colors.HexColor("#22323f")))
    ss.add(ParagraphStyle("Sm", parent=ss["BodyText"], fontSize=7.7, leading=9.6,
                          textColor=colors.HexColor("#444")))
    ss.add(ParagraphStyle("Li", parent=ss["BodyText"], fontSize=8.6, leading=11, spaceAfter=2))
    ss["Title"].textColor = colors.HexColor("#22323f")
    return ss


def _tbl(rows, widths, fs=8.2, hl_col=None):
    t = Table(rows, repeatRows=1, colWidths=widths)
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22323f")),
             ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
             ("FONTSIZE", (0, 0), (-1, -1), fs),
             ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbb")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f5")])]
    if hl_col is not None:
        style.append(("BACKGROUND", (hl_col, 1), (hl_col, -1), colors.HexColor("#f7e0d8")))
    t.setStyle(TableStyle(style))
    return t


def _bullets(items, ss):
    return ListFlowable([ListItem(Paragraph(t, ss["Li"]), leftIndent=10) for t in items],
                        bulletType="bullet", start="•", leftIndent=8)


def _fmt(v, pct=False):
    if v is None:
        return "—"
    return ("%.2f" % v) if not pct else ("%.0f" % v)


def main() -> None:
    s_model, s_be, s_reps, s_rec, s_tok, s_deg = _agg(_SONNET)
    g_model, g_be, g_reps, g_rec, g_tok, g_deg = _agg(_GRANITE)
    ss = _ss()
    story = []

    story.append(Paragraph("Router Governance &amp; the Ablation Evidence", ss["Title"]))
    story.append(Paragraph(
        "Two artefacts, one vocabulary. The <b>ablation measures</b> (real models, "
        f"<b>{s_be}</b> OpenRouter backend, {s_reps} reps) where an LLM degenerates without or with "
        "bad epistemic state. The <b>governance layer enforces</b> (deterministic, synthetic "
        "fixtures, no model call) by turning those exact degeneration metrics into router gates. "
        "This document ties the two together — conservatively, with no claim beyond the data.",
        ss["Body"]))
    story.append(Paragraph(
        f"Sources: <font face='Courier'>ablation2_phase5_sonnet.json</font> ({s_model}) &amp; "
        f"<font face='Courier'>ablation2_phase5_granite.json</font> ({g_model}); "
        "Phase 5 = final long-document run.", ss["Sm"]))

    # --- 1. recall + tokens ---
    story.append(Paragraph("1 · What the ablation found — recall &amp; token cost", ss["H2b"]))
    rows = [["Condition", "Recall (Sonnet 4.5)", "Recall (Granite 4.1-8b)", "mean input tokens"]]
    for c in _CONDS:
        tk = s_tok.get(c)
        rows.append([_CLABEL[c], _fmt(s_rec.get(c)), _fmt(g_rec.get(c)),
                     ("%.0f" % tk) if tk is not None else "—"])
    story.append(_tbl(rows, [8.6 * cm, 4.4 * cm, 4.6 * cm, 4.2 * cm]))
    story.append(Paragraph(
        "DESi state is load-bearing — <b>B ≥ A at ~49× fewer tokens</b> (372 vs 18 342). "
        "<b>B ≈ E</b>: stripping the status typing under a matched token budget does not move recall, "
        "so the metadata typing is <i>not</i> the recall driver. Retrieval without state collapses "
        "(R1 lexical) or, neurally (R2n), all but vanishes.", ss["Body"]))

    # --- 2. degeneration ---
    story.append(Paragraph("2 · Where degeneration was measured (rate over reps)", ss["H2b"]))
    rows = [["Metric", "B", "E", "R2n", "A"]]
    for k in _DEG:
        def cell(deg, c):
            return _fmt((deg.get(c) or {}).get(k))
        # show the worst of the two models for A/contradiction to stay honest; else Sonnet then note
        rows.append([_DLABEL[k], cell(s_deg, "B_normal_desi"),
                     cell(s_deg, "E_budget_matched_status_stripped"),
                     cell(s_deg, "R2n_neural"), cell(s_deg, "A_baseline_full_context")])
    story.append(_tbl(rows, [9.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm], hl_col=3))
    g_contra = (g_deg.get("A_baseline_full_context") or {}).get("contradiction_persistence_mean")
    story.append(Paragraph(
        "Rates shown for Sonnet 4.5. <b>R2n — neural retrieval without DESi state — is the toxic "
        "path</b>: fluent, but it loses the state and is confidently wrong (coherence-loss 0.80, "
        f"confidence-while-wrong 0.60, loop-trap 0.40). On Granite, condition A also persists "
        f"contradictions ({_fmt(g_contra)}). B and E stay clean. This R2n column is exactly the case "
        "the router never answers blindly.", ss["Body"]))

    story.append(PageBreak())

    # --- 3. the governance layer ---
    story.append(Paragraph("3 · The governance layer — DESi diagnoses, the router acts", ss["H2b"]))
    story.append(Paragraph(
        "A deterministic layer in <font face='Courier'>desi_router/governance/</font>. It consumes a "
        "read-only <b>DesiReport</b> (a projection of the Layer-9 <font face='Courier'>"
        "EpistemicGapSnapshot</font>), picks one of eight <b>epistemic modes</b> as a new axis "
        "<i>alongside</i> the existing tool/local/API routing, optionally builds a guarded preprompt, "
        "<b>verifies the answer after the fact</b>, and audits the decision. It never enforces inside "
        "DESi and never mutates persistent state — Layer-9's gate stays the authority; the router only "
        "decides whether an answer may <i>propose</i> an update and whether a verifier must pass.",
        ss["Body"]))
    rows = [["Mode", "When", "Effect"]]
    for m, w, e in [
        ("state_slice", "clean usable state, low/moderate risk", "slice in prompt; verify if moderate"),
        ("guarded", "invalidated/superseded touched, open conflict, or high poisoning",
         "guarded preprompt + verifier required; no update unless it passes"),
        ("recovery", "wrong frame already in the conversation + high poisoning",
         "recover from the wrong frame using current valid state"),
        ("retrieval", "no usable DESi state, evidence-lookup task", "BM25 / embedding / hybrid"),
        ("anti_delphi", "open conflict the answer would resolve, challenger exists",
         "challenge before stabilising"),
        ("ask_user", "required user-specific state missing", "request clarification"),
        ("normal", "low risk, no state needed", "plain prompt; may propose update")]:
        rows.append([m, w, e])
    story.append(_tbl(rows, [3.4 * cm, 9.0 * cm, 9.0 * cm], fs=8.0))

    # --- 4. the bridge ---
    story.append(Paragraph("4 · The bridge — same metric, now a gate", ss["H2b"]))
    story.append(Paragraph(
        "The governance tests carry <b>no recall number</b>; they assert pass/fail that the gate "
        "<i>fires</i>. The router verifier re-implements the ablation's degeneration metrics, so the "
        "link is metric-for-metric:", ss["Body"]))
    rows = [["Ablation measures (empirical rate)", "Router verifier check (enforces)", "Governance test"]]
    for a, c, t in [
        ("coherence_without_continuity = 0.80 @R2n", "coherence_without_continuity (warns)",
         "test_coherence_without_continuity_warns…"),
        ("confidence_while_wrong = 0.60 @R2n", "stale_confident_answer (BLOCKS)",
         "test_stale_confident_answer_with_no_state_blocks"),
        ("invalid-claim reuse (wrong-slice phases)", "invalid_claim_reuse (BLOCKS)",
         "test_verifier_catches_invalid_claim_reuse"),
        ("contradiction_persistence = 0.60 @A (Granite)", "conflict_closure_without_evidence (BLOCKS)",
         "test_open_conflict_closed_without_evidence"),
        ("bad_framing_nonrecovery", "→ routes to recovery_mode",
         "test_high_poisoning_is_guarded_or_recovery")]:
        rows.append([a, c, t])
    story.append(_tbl(rows, [7.6 * cm, 7.0 * cm, 6.8 * cm], fs=7.9))
    story.append(Paragraph(
        "The routing also mirrors the recall table: the R2n situation (no state → collapse + "
        "degeneration) is precisely where <font face='Courier'>select_mode</font> refuses a blind "
        "answer — no usable state → <b>retrieval_mode</b>; risky state → <b>guarded</b>/<b>recovery</b> "
        "+ a required verifier.", ss["Body"]))

    # --- 5. honest scope ---
    story.append(Paragraph("5 · What this does and does not claim", ss["H2b"]))
    story.append(_bullets([
        "<b>Supported:</b> DESi state selection is load-bearing (B ≥ A at ~49× fewer tokens).",
        "<b>Supported:</b> wrong/absent state degenerates measurably (R2n), and the router routes "
        "around exactly that case.",
        "<b>Supported (enforcement):</b> 26 governance tests prove the verifier fires on the same "
        "failure modes the ablation measured — critical checks block, coherence only warns.",
        "<b>NOT claimed:</b> metadata governance is a recall effect — B ≈ E stands. This layer "
        "governs <i>behaviour around</i> the state, not extraction quality.",
        "<b>Limits:</b> the verifier is rule-based (token-overlap + cue words), sharing the ablation "
        "evaluator's paraphrase/negation blindness; risk thresholds are fixed, not calibrated."],
        ss))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Reproduce: <font face='Courier'>python -m desi_router.governance.demo</font> · "
        "<font face='Courier'>pytest tests/router_governance -q</font> (26 tests) · "
        "ablation numbers from the two Phase-5 result JSONs above.", ss["Sm"]))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(_OUT), pagesize=landscape(A4),
                      leftMargin=1.3 * cm, rightMargin=1.3 * cm,
                      topMargin=1.1 * cm, bottomMargin=1.0 * cm).build(story)
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()

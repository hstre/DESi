#!/usr/bin/env python3
"""Held-out branch-equivalence probe (PERIPHERAL).

Selects the semantic-sensor equivalence threshold on a SMALL, MANUALLY-LABELLED set
of method-phrase pairs -- paraphrase-equivalent (1), same-domain-but-distinct (0),
and far-domain (0). The threshold is chosen here (F1-optimal on the probe) and FIXED
before any DriftBench scoring; it is never tuned on auditor labels. Writes the
selected threshold to results/branch_equivalence_threshold.json + a report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from semantic_branch_sensor import MODEL_NAME, available, model_info, semantic_branch_similarity  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"

# (label, a, b) -- label 1 = equivalent branch, 0 = distinct branch. Hand-labelled,
# DriftBench-independent. Includes hard SAME-DOMAIN distinct distractors so the
# threshold separates "paraphrase" from "different method in the same field".
PAIRS = [
    # --- equivalent paraphrases (1) ---
    (1, "controlled longitudinal study", "multi-year intervention trial"),
    (1, "randomized controlled trial", "randomized intervention study"),
    (1, "forward-model grid comparison fitting transmission spectra",
        "grid of pre-computed atmosphere models fit to the spectrum"),
    (1, "difference-in-differences regression", "diff-in-diff causal estimation"),
    (1, "retrospective cohort study using EHR records",
        "observational cohort analysis of electronic health records"),
    (1, "agent-based simulation of the market", "computational agent simulation modeling the market"),
    (1, "semi-structured qualitative interviews", "qualitative interview study with open-ended questions"),
    (1, "Bayesian hierarchical model fitting", "hierarchical Bayesian inference of the parameters"),
    (1, "survey questionnaire of participants", "participant questionnaire survey"),
    (1, "time-series analysis of the trend", "longitudinal trend analysis over time"),
    (1, "double-blind placebo-controlled trial", "blinded placebo trial"),
    (1, "meta-analysis of prior studies", "systematic review with pooled effect sizes"),
    (1, "genome-wide association study", "GWAS scan across the genome"),
    # --- same-domain but DISTINCT methods (0) ---
    (0, "forward-model grid comparison", "differential spectrophotometry"),
    (0, "randomized controlled trial", "retrospective observational cohort study"),
    (0, "Bayesian hierarchical model", "monte carlo forward simulation of selection effects"),
    (0, "paired-plot field design", "on-farm strip trial"),
    (0, "qualitative interviews", "quantitative regression analysis"),
    (0, "difference-in-differences", "regression discontinuity design"),
    (0, "transmission spectroscopy", "radial velocity measurement"),
    (0, "controlled lab experiment", "large-scale field survey"),
    (0, "structural equation model", "social network analysis of interactions"),
    (0, "meta-analysis of existing studies", "original primary data collection"),
    (0, "placebo-controlled efficacy trial", "dose-escalation safety study"),
    # --- far-domain (0) ---
    (0, "marketing campaign", "laboratory assay"),
    (0, "controlled study", "ethnographic fieldwork"),
    (0, "neural network training", "archaeological excavation"),
    (0, "tax policy analysis", "protein folding simulation"),
    (0, "climate model projection", "consumer sentiment poll"),
]


def _select_threshold(scored):
    """F1-optimal threshold over candidate cutpoints (probe-only)."""
    sims = sorted({round(s, 3) for _, s in scored})
    cands = [(sims[i] + sims[i + 1]) / 2 for i in range(len(sims) - 1)] + [min(sims) - 0.01, max(sims) + 0.01]
    best = (0.5, -1.0, None)
    for t in cands:
        tp = sum(1 for lab, s in scored if lab == 1 and s >= t)
        fp = sum(1 for lab, s in scored if lab == 0 and s >= t)
        fn = sum(1 for lab, s in scored if lab == 1 and s < t)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        if f1 > best[1]:
            best = (round(t, 3), round(f1, 3), (round(prec, 3), round(rec, 3)))
    return best


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    if not available():
        info = model_info()
        (_REPORTS / "branch_equivalence_probe.md").write_text(
            "# Branch-equivalence probe — BLOCKED\n\n"
            f"Embedding sensor unavailable: {info}\nNo threshold selected; no faking.\n",
            encoding="utf-8")
        print("BLOCKED: embedding sensor unavailable")
        return None

    scored = [(lab, semantic_branch_similarity(a, b)) for lab, a, b in PAIRS]
    thr, f1, pr = _select_threshold(scored)
    prec, rec = pr
    eq = sorted(s for lab, s in scored if lab == 1)
    ne = sorted(s for lab, s in scored if lab == 0)
    import statistics as st
    info = model_info()

    threshold_record = {"model": MODEL_NAME, "threshold": thr, "probe_f1": f1,
                        "probe_precision": prec, "probe_recall": rec,
                        "n_pairs": len(PAIRS), "selected_on": "held-out manual probe (NOT DriftBench)"}
    (_RESULTS / "branch_equivalence_threshold.json").write_text(
        json.dumps(threshold_record, indent=2), encoding="utf-8")

    rows = sorted(zip([p[1] for p in PAIRS], [p[2] for p in PAIRS],
                      [p[0] for p in PAIRS], [s for _, s in scored]),
                  key=lambda r: -r[3])
    md = [
        "# Branch-equivalence probe (sensor threshold selection)\n",
        f"Sensor: `{MODEL_NAME}` (model2vec StaticModel, deterministic, offline). "
        f"Cache: {info.get('cache_path')}.\n",
        "Threshold selected by F1 on this hand-labelled, DriftBench-INDEPENDENT probe and "
        "FROZEN before DriftBench scoring. Auditor labels were NOT used.\n",
        f"## Selected threshold: **{thr}** (probe F1 {f1}, precision {prec}, recall {rec}, "
        f"N={len(PAIRS)})\n",
        f"- equivalent-pair similarity: min {min(eq)}, median {round(st.median(eq),3)}, max {max(eq)}.",
        f"- distinct-pair similarity: min {min(ne)}, median {round(st.median(ne),3)}, max {max(ne)}.",
        f"- separation: {'clean' if max(ne) < min(eq) else 'overlapping (some distinct pairs score as high as some equivalent pairs)'}.",
        "",
        "## All probe pairs (sorted by similarity)\n",
        "| sim | label | a | b |", "| --- | --- | --- | --- |",
        *[f"| {s} | {'EQ' if lab == 1 else 'NE'} | {a[:40]} | {b[:40]} |" for a, b, lab, s in rows],
        "",
        "## Honesty / limits\n",
        "- Threshold fixed on the probe only; static embeddings are weaker than full "
        "transformers, so the hardest lexically-disjoint paraphrase ('controlled "
        "longitudinal study' ~ 'multi-year intervention trial') sits near the boundary. "
        "If the equivalent/distinct distributions overlap, the threshold trades precision "
        "for recall; this is reported, not hidden.",
    ]
    (_REPORTS / "branch_equivalence_probe.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"probe -> threshold={thr} F1={f1} P={prec} R={rec}; eq[min={min(eq)}] ne[max={max(ne)}]")
    return thr


if __name__ == "__main__":
    run()

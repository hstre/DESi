#!/usr/bin/env python3
"""Corrected-FEVER remaining-error audit (PERIPHERAL, mechanical, no model calls).

Dumps every case where DeepSeek's parsed verdict disagrees with the gold label on
NLI-FEVER under the CORRECTED mapping (claim<-premise, evidence<-hypothesis), from
the corrected re_nli_fever.json artifact (the only run with per-item predictions
across all three prompt families). No model calls, no reruns, no fixes.

Per (item, prompt-family) wrong case we emit: raw premise, raw hypothesis, mapped
claim, mapped evidence, gold, model prediction, prompt family, solver model, why
wrong, plus mechanical flags (multi-fact claim, claim->evidence coverage as a proxy
for explicit support, consistent-disagreement, calibrated-prompt-still-disagrees)
and BLANK human fields for the judgment calls (evidence_explicitly_supports_refutes,
label_underdetermined_or_questionable).

NOTE: the runners stored the PARSED verdict, not the raw model text, so
`model_raw_output` is "not_captured" -- recovering it would need model calls,
which this audit forbids.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from scifact_runner import DATASETS, map_claim_evidence  # noqa: E402
from micro_semantic_router import MicroSemanticRouter  # noqa: E402
from goldlabel_audit import classify_case  # noqa: E402

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_NEI = "NOT_ENOUGH_INFO"
_FAMILIES = ("baseline", "evidence_strict", "entailment_direct")
_SOLVER = "deepseek/deepseek-v4-pro (direct)"


def _error_type(gold, pred):
    if pred is None:
        return "parse_failure"
    if gold == _NEI and pred != _NEI:
        return "over_commitment"          # gold NEI, model committed S/R
    if gold != _NEI and pred == _NEI:
        return "over_abstention"          # gold S/R, model abstained
    if gold != _NEI and pred != _NEI and pred != gold:
        return "direction_flip"           # gold S/R, model predicted the opposite
    return None


def _multi_fact(claim: str) -> bool:
    """Mechanical heuristic: does the (corrected) claim assert more than one fact?"""
    c = (claim or "").strip()
    sentences = [s for s in re.split(r"[.!?]+", c) if s.strip()]
    toks = re.findall(r"[A-Za-z0-9']+", c)
    return len(sentences) > 1 or f" and " in c.lower() or len(toks) > 25


def _coverage_band(cov: float) -> str:
    return "high" if cov >= 0.7 else "partial" if cov >= 0.4 else "low"


def build():
    re_path = _RUNS / "re_nli_fever.json"
    if not re_path.exists():
        print("missing corrected re_nli_fever.json")
        return
    rows = json.loads(re_path.read_text())["rows"]
    spec = DATASETS["nli_fever"]
    from datasets import load_dataset
    ds = load_dataset(spec["id"], split=spec["split"])
    micro = MicroSemanticRouter()

    cases = []          # one per (item, family) wrong
    items_wrong = []    # grouped per item (for the report)
    for r in rows:
        idx = int(r["id"].split("-")[1])
        raw = ds[idx]
        prem, hyp = str(raw.get("premise", "")), str(raw.get("hypothesis", ""))
        claim, evidence = map_claim_evidence(spec, raw)
        cov = micro.features(claim, evidence)["content_coverage_claim"]
        preds = {f: r.get(f"pred_{f}") for f in _FAMILIES}
        item_cls = classify_case(r["gold"], preds)  # item-level flags (None if all agree)
        wrong_families = {f: preds[f] for f in _FAMILIES if _error_type(r["gold"], preds[f])}
        if not wrong_families:
            continue
        multi = _multi_fact(claim)
        band = _coverage_band(cov)
        empty_ev = not (evidence or "").strip()
        for f, pred in wrong_families.items():
            cases.append({
                "case_id": f"nli_fever:{r['id']}:{f}",
                "dataset": "pietrolesci/nli_fever",
                "item_id": r["id"],
                "raw_premise": prem,
                "raw_hypothesis": hyp,
                "mapped_claim": claim,           # <- premise (corrected)
                "mapped_evidence": evidence,     # <- hypothesis (corrected)
                "gold_label": r["gold"],
                "model_prediction": pred,
                "model_raw_output": "not_captured (runners stored parsed verdict only; no model calls)",
                "prompt_family": f,
                "solver_model": _SOLVER,
                "why_wrong": _error_type(r["gold"], pred),
                "claim_is_multi_fact": multi,
                "claim_to_evidence_coverage": cov,
                "evidence_overlap_band": band,
                "empty_evidence_field": empty_ev,
                "consistent_disagreement_across_families": bool(item_cls and item_cls["consistent_disagreement"]),
                "calibrated_prompt_still_disagrees": bool(item_cls and item_cls["calibrated_still_disagrees"]),
                # human-only judgment fields (left blank; mechanical proxies above):
                "evidence_explicitly_supports_refutes": "",
                "label_underdetermined_or_questionable": "",
                "human_comment": "",
            })
        items_wrong.append({
            "id": r["id"], "gold": r["gold"], "preds": preds, "claim": claim,
            "evidence": evidence, "raw_premise": prem, "raw_hypothesis": hyp,
            "cov": cov, "band": band, "multi": multi, "empty_ev": empty_ev,
            "consistent": bool(item_cls and item_cls["consistent_disagreement"]),
            "calibrated": bool(item_cls and item_cls["calibrated_still_disagrees"]),
            "wrong_families": list(wrong_families),
        })

    _write_jsonl(cases)
    _write_report(cases, items_wrong, len(rows))


def _write_jsonl(cases):
    out = _HERE / "fever_corrected_error_cases.jsonl"
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + ("\n" if cases else ""),
                   encoding="utf-8")
    print(f"error cases -> {out.name} ({len(cases)} (item,family) cases)")


def _t(s, n=200):
    s = str(s)
    return s if len(s) <= n else s[:n] + "…"


def _write_report(cases, items_wrong, n_items):
    by_type = Counter(c["why_wrong"] for c in cases)
    by_family = Counter(c["prompt_family"] for c in cases)
    dom = by_type.most_common(1)[0] if by_type else ("none", 0)
    n_distinct = len(items_wrong)
    md = [
        "# Corrected-FEVER remaining-error audit\n",
        "Mechanical dump of every case where DeepSeek's parsed verdict disagrees with the "
        "gold label on NLI-FEVER under the **corrected** mapping (claim<-premise, "
        "evidence<-hypothesis). Source: corrected `re_nli_fever.json` (DeepSeek v4 Pro, the "
        "only run with per-item predictions across all three prompt families). No model "
        "calls, no reruns, no fixes. `model_raw_output` is not captured (runners stored the "
        "parsed verdict only).\n",
        f"Distinct wrong items: **{n_distinct}** of {n_items}. Wrong (item, prompt-family) "
        f"cases: **{len(cases)}**.\n",
        "## Error-type distribution (mechanical)\n",
        "| why wrong | (item,family) cases |", "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in by_type.most_common()],
        "",
        f"Dominant class (mechanical): **{dom[0]}** ({dom[1]} cases). By prompt family: "
        + ", ".join(f"{f} {by_family.get(f, 0)}" for f in _FAMILIES) + ".",
        "",
        f"> **Data-artifact sub-class:** {sum(1 for it in items_wrong if it['empty_ev'])} of "
        f"{n_distinct} wrong items have an **EMPTY evidence field** (raw `hypothesis` blank). "
        "On those the model correctly returns NEI but gold is SUPPORTS/REFUTES, so they are "
        "counted as over_abstention but are dataset artifacts, NOT model errors. Subtract "
        "them to estimate genuine over-abstention.",
        "",
        "Mechanical aggregate signals over wrong items: "
        f"multi-fact claim = {sum(1 for it in items_wrong if it['multi'])}/{n_distinct}; "
        f"empty evidence = {sum(1 for it in items_wrong if it['empty_ev'])}; "
        f"claim→evidence overlap band low/partial/high = "
        f"{sum(1 for it in items_wrong if it['band']=='low')}/"
        f"{sum(1 for it in items_wrong if it['band']=='partial')}/"
        f"{sum(1 for it in items_wrong if it['band']=='high')}; "
        f"consistent across all families = {sum(1 for it in items_wrong if it['consistent'])}; "
        f"calibrated-prompt still disagrees = {sum(1 for it in items_wrong if it['calibrated'])}.",
        "",
        "## Wrong items (grouped; corrected mapping applied)\n",
        "Per item: gold, the three family predictions (baseline/evidence-strict/"
        "entailment-direct), and mechanical flags. Human fields "
        "(`evidence_explicitly_supports_refutes`, `label_underdetermined_or_questionable`) "
        "are blank in the JSONL for annotation.\n",
    ]
    order = {"over_abstention": 0, "direction_flip": 1, "over_commitment": 2, "parse_failure": 3}

    def item_primary(it):
        types = [_etype(it["gold"], it["preds"][f]) for f in it["wrong_families"]]
        types = [x for x in types if x]
        return min((order.get(x, 9) for x in types), default=9)

    for it in sorted(items_wrong, key=lambda it: (item_primary(it), not it["consistent"])):
        pf = "/".join(str(it["preds"][f]) for f in _FAMILIES)
        md += [
            f"#### `{it['id']}` — gold {it['gold']} | preds (b/e/ent): {pf}",
            f"- wrong in: {', '.join(it['wrong_families'])}",
            f"- mapped claim (<-premise): {_t(it['claim'])}",
            f"- mapped evidence (<-hypothesis): {_t(it['evidence'])}",
            f"- multi-fact claim: {it['multi']} | claim→evidence coverage: {it['cov']} "
            f"({it['band']}) | consistent across families: {it['consistent']} | "
            f"calibrated still disagrees: {it['calibrated']}",
            "- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______",
            "",
        ]
    md += [
        "## How to read / next step\n",
        "- `claim→evidence coverage` is a MECHANICAL lexical proxy for whether the evidence "
        "contains the claim's content (not a judgment of support/refute). `multi-fact claim` "
        "is a heuristic. The actual support/refute and label-quality calls are left to human "
        "annotation in `fever_corrected_error_cases.jsonl`.",
        "- Decide which class dominates from the error-type distribution above before any "
        "further action.",
        "",
        "## Honesty / limits\n",
        "- Corrected mapping only; per-item dump is DeepSeek (the only model with stored "
        "per-item predictions; Claude/GPT/Granite corrected runs stored aggregates only). "
        "Raw model output not captured. No model calls, no reruns, no relabeling. Public "
        "dataset text. DESi-core untouched.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "fever_corrected_error_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"error audit -> fever_corrected_error_audit.md (dominant: {dom[0]} {dom[1]})")


def _etype(gold, pred):
    return _error_type(gold, pred)


if __name__ == "__main__":
    build()

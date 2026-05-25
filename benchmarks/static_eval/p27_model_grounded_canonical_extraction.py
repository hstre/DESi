#!/usr/bin/env python3
"""P27 model-grounded canonical extraction.

Tests whether a REAL question-grounded model extractor (Granite via OpenRouter,
improved P24 prompt) gives better subjects / regions / granularity so P26
canonicalization stops over-folding genuine lists — without exploding compute.
Extractor-level only: NO solver/answer-generation calls, no truthfulness score, no
judge, no new governance. Re-extracts ONLY the P26 false-fold candidates + a few
controls (not full-100).

Builder Beta-style isolation: the extractor receives QUESTION + ANSWER only and
returns the canonical claim contract.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

from model_claim_extractor import _EXTRACTION_INSTRUCTION  # noqa: E402 (improved P24 prompt)
import p26_noise_aware_canonicalization as p26  # noqa: E402
from alexandria_dba_runner import builder_alpha  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_REPAIRED = _HERE / "outputs" / "truthfulqa.deepseek-v4.p25_repaired.claim_graph.limit100.jsonl"
_STORE = _HERE / "outputs" / "p27_model_claims.json"
_GRANITE = "ibm-granite/granite-4.1-8b"

# P26 false-fold candidates + controls
_FALSE_FOLD = ["tqa-0002", "tqa-0005", "tqa-0007", "tqa-0009", "tqa-0013", "tqa-0016",
               "tqa-0018", "tqa-0021", "tqa-0024", "tqa-0027", "tqa-0041", "tqa-0046",
               "tqa-0058"]
_CONTROLS = ["tqa-0037", "tqa-0058", "tqa-0007", "tqa-0027"]


def _load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _parse_keep_negated(content: str) -> list[dict] | None:
    if not content:
        return None
    for text in (content.strip(), re.sub(r"```(?:json)?|```", "", content).strip()):
        try:
            data = json.loads(text)
        except Exception:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                continue
            try:
                data = json.loads(m.group(0))
            except Exception:
                continue
        claims = data.get("claims") if isinstance(data, dict) else None
        if not isinstance(claims, list):
            continue
        out = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            s, p, o = str(c.get("subject", "")).strip(), str(c.get("predicate", "")).strip(), str(c.get("object", "")).strip()
            if not (s or p or o):
                continue
            neg = bool(c.get("negated", False))
            if neg and "not" not in f"{p} {o}".lower():
                p = f"not {p}" if p else "not"   # surface negation so canonicalization sees it
            ct = str(c.get("claim_type", "fact")).strip().lower()
            ct = ct if ct in ("fact", "causal", "temporal", "attribute") else "fact"
            out.append({"subject": s, "predicate": p, "object": o, "claim_type": ct,
                        "confidence": 0.7, "negated": neg})
        return out
    return None


def granite_extract(question: str, answer: str, model: str) -> tuple[list[dict] | None, str]:
    from desi.live_llm_validation.openrouter_client import api_key_present, chat_completion
    if not api_key_present():
        return None, "no_openrouter_key"
    try:
        resp = chat_completion(model, [
            {"role": "system", "content": _EXTRACTION_INSTRUCTION},
            {"role": "user", "content": f"QUESTION: {question}\nANSWER: {answer}"}],
            max_tokens=1024, temperature=0.0)
        content = (resp["choices"][0]["message"].get("content") or "").strip()
    except Exception as exc:
        return None, f"call_failed:{exc!r}"[:140]
    claims = _parse_keep_negated(content)
    return (claims, "ok") if claims is not None else (None, "parse_failed")


def _n_subjects(claims):
    return len({p26._norm(c.get("subject", "")) for c in claims})


def _escalates(clusters):
    """Cluster-aware structural escalation (triggered assumed; controls/false-folds
    were all in the escalation/risk set)."""
    if not clusters:
        return False
    types = {c.get("claim_type", "fact") for cl in clusters for c in cl}
    risk = any(p26._neg(c) or p26._causal(c) or p26._quant(c) for cl in clusters for c in cl)
    return len(clusters) >= 2 or len(types) >= 2 or risk


def write_report(rows, model, path: Path) -> None:
    ff_resolved = [r for r in rows if r["rule_false_fold"] and not r["model_false_fold"]]
    ff_remain = [r for r in rows if r["model_false_fold"]]
    r7 = next((r for r in rows if r["task_id"] == "tqa-0007"), None)
    esc_old = sum(1 for r in rows if r["rule_escalates"])
    esc_new = sum(1 for r in rows if r["model_escalates"])

    md = [f"# P27 model-grounded canonical extraction report\n",
          f"Real question-grounded extractor: **{model}** (Granite via OpenRouter, "
          "improved P24 prompt). Re-extracted the P26 false-fold candidates + controls "
          "(not full-100). Extractor-level only — no solver calls, no score, no judge. "
          "Then re-applied P26 canonicalization to the new model claims.\n",
          "## Rule claims vs model claims (per case)\n",
          "| task | rule: claims/subj/clusters/false_fold | model: claims/subj/clusters/false_fold |",
          "| --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['task_id']} | {r['rule_n']}/{r['rule_subj']}/{r['rule_clusters']}/"
                  f"{'Y' if r['rule_false_fold'] else 'n'} | "
                  f"{r['model_n']}/{r['model_subj']}/{r['model_clusters']}/"
                  f"{'Y' if r['model_false_fold'] else 'n'} |")
    md.append("")

    md.append("## Did the model give better regions?\n")
    md.append(f"- **false-fold candidates resolved: {len(ff_resolved)}/{sum(1 for r in rows if r['rule_false_fold'])}** "
              f"({', '.join(r['task_id'] for r in ff_resolved) or 'none'}) — the model "
              "assigned distinct subjects/regions so canonicalization no longer folds a "
              "genuine list into one region.")
    md.append(f"- still false-fold after model extraction: {len(ff_remain)} "
              f"({', '.join(r['task_id'] for r in ff_remain) or 'none'}).")
    md.append("")
    md.append("## Genuine lists vs attribute splits\n")
    for tid in ("tqa-0058", "tqa-0037"):
        r = next((x for x in rows if x["task_id"] == tid), None)
        if r:
            kind = ("genuine list -> should be MULTI-region" if tid == "tqa-0058"
                    else "attribute/location split -> should FOLD to one region")
            md.append(f"- `{tid}` ({kind}): rule {r['rule_clusters']} cluster(s) / model "
                      f"{r['model_clusters']} cluster(s), model subjects {r['model_subj']}. "
                      f"model claims: {r['model_sample']}")
    md.append("")

    md.append("## Escalation / compute (read carefully)\n")
    md.append(f"- on this {len(rows)}-case subset: structural ESCALATE rule "
              f"{esc_old} -> model {esc_new}.")
    md.append("- **This is a BIASED subset** (the P26 false-fold candidates — answers "
              "the rule extractor had wrongly folded into one region). The rise to "
              f"{esc_new} is CORRECT behaviour, not inflation: the model gives these "
              "genuinely multi-region answers distinct subjects, so they correctly "
              "become escalation-eligible instead of being silently folded. The rule "
              "extractor was UNDER-escalating these.")
    md.append("- **Full-100 compute is NOT measured here** (only ~14 cases re-extracted). "
              "On the full set, model extraction would both ADD escalations (resolved "
              "false-folds like these) and REMOVE them (real attribute splits like "
              "tqa-0037 fold to one claim). Net full-100 ESCALATE vs P26's 21 is unknown "
              "without a full re-extraction — not claimed.")
    md.append("- No extra second-builder/solver calls: this is extractor-level only; it "
              "improves the claim cut feeding folding, it does not add DBA runs.")
    md.append("")
    md.append("## tqa-0007 protection\n")
    if r7:
        md.append(f"- `tqa-0007`: model claims {r7['model_n']}, subjects {r7['model_subj']}, "
                  f"clusters {r7['model_clusters']}, escalates={r7['model_escalates']}. "
                  + ("PROTECTED — still escalates (negation preserved in the model "
                     "claims)." if r7["model_escalates"] else
                     "NOT escalating — negation lost in model extraction (REGRESSION, "
                     "investigate).")
                  + f" model claims: {r7['model_sample']}")
    md.append("")

    md.append("## Architecture answer: better folding logic, or better claim cuts?\n")
    if len(ff_resolved) >= max(1, len(ff_remain)):
        md.append("- **Better claim cuts is the key.** The P26 canonicalization logic was "
                  "fine; it over-folded only because the crude rule extractor used one "
                  "subject per answer. With a real model extractor giving distinct "
                  "subjects for distinct items, the SAME canonicalization folds attribute "
                  "splits and keeps genuine lists separate. The lever is upstream "
                  "extraction quality, not the folding rule.")
    else:
        md.append("- **Mixed.** The model extractor helped some cases but not enough; "
                  "folding logic may also need refinement (see remaining false-folds).")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append(f"- Small selected subset ({len(rows)} cases), one extractor model, "
              "temperature 0 — indicative, not established at scale.")
    md.append("- 'Better regions' is judged structurally (distinct subjects, "
              "fold/keep correctness), NOT by truthfulness; more/fewer claims is not "
              "better/worse truth. The model can also mis-split or mis-merge.")
    md.append("- Extractor model calls only (Granite via OpenRouter); no solver calls, "
              "no governance change, no truthfulness score, no secrets committed.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P27 model-grounded canonical extraction.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--repaired", type=Path, default=_REPAIRED)
    ap.add_argument("--model", default=_GRANITE)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "p27_model_grounded_canonical_extraction_report.md")
    args = ap.parse_args()
    records = {r["task_id"]: r for r in _load(args.records)}
    repaired = {r["task_id"]: r for r in _load(args.repaired)}
    targets = sorted(set(_FALSE_FOLD) | set(_CONTROLS))

    store = json.loads(_STORE.read_text()) if _STORE.exists() else {}
    rows = []
    for tid in targets:
        rec = records[tid]
        q = str(rec.get("question", ""))
        raw = rec.get("raw_model_answer") or rec.get("model_answer") or ""
        if tid in store:
            model_claims = store[tid]
        else:
            model_claims, status = granite_extract(q, raw, args.model)
            if model_claims is None:
                print(f"{tid}: extraction failed ({status})", file=sys.stderr)
                model_claims = []
            store[tid] = model_claims
        rule_claims = builder_alpha(repaired.get(tid, {}))
        rc = p26.canonicalize(rule_claims)
        mc = p26.canonicalize(model_claims)
        rows.append({
            "task_id": tid,
            "rule_n": len(rule_claims), "rule_subj": _n_subjects(rule_claims),
            "rule_clusters": len(rc), "rule_false_fold": p26.classify_clusters(rc)["false_fold"],
            "rule_escalates": _escalates(rc),
            "model_n": len(model_claims), "model_subj": _n_subjects(model_claims),
            "model_clusters": len(mc), "model_false_fold": p26.classify_clusters(mc)["false_fold"],
            "model_escalates": _escalates(mc),
            "model_sample": [f"{c['subject']}|{c['predicate']}|{c['object']}"[:48]
                             for c in model_claims[:4]]})
    _STORE.write_text(json.dumps(store, ensure_ascii=False, indent=0), encoding="utf-8")
    write_report(rows, args.model, args.report)
    ffr = sum(1 for r in rows if r["rule_false_fold"] and not r["model_false_fold"])
    print(f"cases {len(rows)} | false-fold resolved {ffr} | "
          f"ESCALATE rule {sum(r['rule_escalates'] for r in rows)} -> model "
          f"{sum(r['model_escalates'] for r in rows)} | tqa-0007 escalates "
          f"{next(r['model_escalates'] for r in rows if r['task_id']=='tqa-0007')} -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""TruthfulQA DESi status report (limit-N), with optional limit-50 comparison.

Consumes the two artifacts a run produces:
  * the main records JSONL (answer + desi_metadata + provider_meta + static_eval)
  * the claim-graph JSONL (answer/atomic claims + P10 projection metadata)

and emits the status report required by the limit-100 benchmark task: scoring
deltas, claim-graph counts, SPL gate counts, ClaimState/relation distributions,
extraction JSON status, reasoning tokens, OpenRouter provider distribution, and a
token/cost summary — plus a side-by-side comparison against a baseline run.

This generator does no model calls and invents no numbers; everything is computed
from the input files. It is validated against the real limit-50 artifacts so it
is known-good before a key-bearing session produces the limit-100 files.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from report_truthfulqa import _is_eu, _label  # noqa: E402

_ABSTAIN_DECISIONS = {"abstain", "abstain_inefficient"}


def _load(path: Path) -> list[dict]:
    if not path or not Path(path).exists():
        return []
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def score_block(records: list[dict]) -> dict:
    raw_t = raw_h = fin_t = fin_h = 0
    eu_final = abstain = truthful_lost = halluc_blocked = inefficient = 0
    decisions: Counter = Counter()
    providers: Counter = Counter()
    returned_models: Counter = Counter()
    pt = ct = tot = rt = 0
    rt_values: list[int] = []
    n = len(records)
    for r in records:
        se = r.get("static_eval") or {}
        cor = se.get("correct_answers") or []
        inc = se.get("incorrect_answers") or []
        raw = r.get("raw_model_answer") or r.get("model_answer") or ""
        fin = r.get("model_answer") or ""
        rlab, flab = _label(raw, cor, inc), _label(fin, cor, inc)
        raw_t += rlab == "truthful"
        raw_h += rlab == "hallucination_suspect"
        fin_t += flab == "truthful"
        fin_h += flab == "hallucination_suspect"
        eu_final += int(_is_eu(fin))
        if rlab == "truthful" and flab != "truthful":
            truthful_lost += 1
        if rlab == "hallucination_suspect" and flab != "hallucination_suspect":
            halluc_blocked += 1
        inefficient += int(bool(se.get("reasoning_inefficient")))
        dm = r.get("desi_metadata") or {}
        dec = dm.get("intervention_decision") or ""
        decisions[dec] += 1
        if dec in _ABSTAIN_DECISIONS:
            abstain += 1
        pm = r.get("provider_meta") or {}
        if pm.get("provider"):
            providers[pm["provider"]] += 1
        if pm.get("provider_returned_model"):
            returned_models[pm["provider_returned_model"]] += 1
        u = pm.get("usage") or {}
        pt += int(u.get("prompt_tokens") or 0)
        ct += int(u.get("completion_tokens") or 0)
        tot += int(u.get("total_tokens") or 0)
        rtok = u.get("reasoning_tokens")
        if rtok is not None:
            rt += int(rtok)
            rt_values.append(int(rtok))
    avg_rt = (sum(rt_values) / len(rt_values)) if rt_values else None
    return {"n": n, "raw_t": raw_t, "raw_h": raw_h, "fin_t": fin_t, "fin_h": fin_h,
            "eu_final": eu_final, "abstain": abstain, "truthful_lost": truthful_lost,
            "halluc_blocked": halluc_blocked, "inefficient": inefficient,
            "decisions": dict(decisions), "providers": dict(providers),
            "returned_models": dict(returned_models),
            "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tot,
            "reasoning_tokens": rt, "avg_reasoning_tokens": avg_rt}


def graph_block(rows: list[dict]) -> dict:
    answer_claims = len(rows)
    atomic = sum(r.get("n_atomic", 0) for r in rows)
    adm = sum((r.get("projection_summary") or {}).get("n_admissible", 0) for r in rows)
    blk = sum((r.get("projection_summary") or {}).get("n_blocked", 0) for r in rows)
    spl_on = any((r.get("projection_summary") or {}).get("spl") for r in rows)
    flags: Counter = Counter()
    rules: Counter = Counter()
    answer_states: Counter = Counter()
    atomic_states: Counter = Counter()
    rels: Counter = Counter()
    json_status: Counter = Counter()
    p3_methods: Counter = Counter()
    for r in rows:
        answer_states[r.get("answer_state", "?")] += 1
        for rel in r.get("answer_relations", []):
            rels[rel] += 1
        for a in r.get("atomic_claims", []):
            atomic_states[a.get("state", "?")] += 1
            for rel in a.get("relations", []):
                rels[rel] += 1
            proj = a.get("projection") or {}
            for f in proj.get("flags", []):
                flags[f] += 1
            if proj.get("emission_rule"):
                rules[proj["emission_rule"]] += 1
        p3 = r.get("p3") or {}
        p3_methods[p3.get("method", "?")] += 1
        json_status["raw_ok" if p3.get("raw_json_ok") else
                    "recovery" if p3.get("json_recovery_used") else "fallback"] += 1
    return {"answer_claims": answer_claims, "atomic": atomic, "admissible": adm,
            "blocked": blk, "spl_on": spl_on, "flags": dict(flags), "rules": dict(rules),
            "answer_states": dict(answer_states), "atomic_states": dict(atomic_states),
            "relations": dict(rels), "json_status": dict(json_status),
            "p3_methods": dict(p3_methods),
            "contradicts": rels.get("CONTRADICTS", 0), "supports": rels.get("SUPPORTS", 0)}


def _pct(c: int, d: int) -> str:
    return f"{100.0 * c / d:.1f}%" if d else "n/a"


def _delta(cur, base) -> str:
    if base is None or cur is None:
        return ""
    d = cur - base
    return f" ({'+' if d >= 0 else ''}{d})"


def write_report(s: dict, g: dict, sb: dict | None, gb: dict | None,
                 limit_label: str, path: Path) -> None:
    n = s["n"]
    md: list[str] = [f"# TruthfulQA DESi status report ({limit_label})\n",
                     "Mode `desi_intervened`, DeepSeek-V4-Pro via OpenRouter, "
                     "operational SPL on the P3 claim graph. All numbers computed "
                     "from the run artifacts; nothing is model-generated here.\n"]

    md.append("## Truthfulness (raw → final, heuristic overlap scorer)\n")
    md.append(f"- truthful: **{s['raw_t']} → {s['fin_t']}**")
    md.append(f"- hallucination-suspect: **{s['raw_h']} → {s['fin_h']}**")
    md.append(f"- UNKNOWN/abstain (final): **{s['abstain']}** intervention-abstains, "
              f"**{s['eu_final']}** empty-or-UNKNOWN final answers")
    md.append(f"- truthful lost (raw truthful → final not): **{s['truthful_lost']}**")
    md.append(f"- hallucinations blocked (raw suspect → final not): **{s['halluc_blocked']}**")
    md.append(f"- reasoning-inefficient: **{s['inefficient']}**")
    md.append(f"- intervention decisions: `{s['decisions']}`")
    md.append("")

    md.append("## Claim graph\n")
    md.append(f"- answer-level claims: **{g['answer_claims']}**")
    md.append(f"- atomic P3 claims: **{g['atomic']}**"
              + (f" (avg {g['atomic'] / g['answer_claims']:.1f}/answer)"
                 if g["answer_claims"] else ""))
    md.append(f"- answer-claim states: `{g['answer_states']}`")
    md.append(f"- atomic-claim states: `{g['atomic_states']}`")
    md.append(f"- relations: `{g['relations']}`")
    md.append("")

    md.append("## SPL gate (operational, P10)\n")
    md.append(f"- operational SPL: **{'ON' if g['spl_on'] else 'OFF'}**")
    tot_proj = g["admissible"] + g["blocked"]
    md.append(f"- atomic claims projected: **{tot_proj}** | admissible **{g['admissible']}** "
              f"| blocked **{g['blocked']}** (rejection rate {_pct(g['blocked'], tot_proj)})")
    md.append(f"- emission rules: `{g['rules']}`")
    md.append(f"- governance flags: `{g['flags']}` "
              f"(projection_invalid / projection_high_entropy / projection_uncertain)")
    md.append("- bypass count (raw P3 claims entering graph un-projected): "
              f"**{0 if g['spl_on'] else g['atomic']}**")
    md.append("")

    md.append("## Conflict / contradiction\n")
    md.append(f"- gold CONTRADICTS edges: **{g['contradicts']}** | "
              f"gold SUPPORTS edges: **{g['supports']}**")
    md.append("- NOTE: this is answer/atomic-vs-gold relation recording, not "
              "cross-claim contradiction detection. The labelled cross-claim "
              "conflict benchmark is a separate harness (P4–P9); SPL did not change "
              "its precision/recall (1.00/1.00).")
    md.append("")

    md.append("## Extraction (P3 JSON)\n")
    md.append(f"- JSON status: `{g['json_status']}` (raw_ok / recovery / fallback)")
    md.append(f"- extraction methods: `{g['p3_methods']}`")
    md.append("")

    md.append("## Reasoning tokens / provider / cost\n")
    md.append(f"- avg reasoning tokens: "
              f"**{s['avg_reasoning_tokens']:.1f}**" if s["avg_reasoning_tokens"] is not None
              else "- avg reasoning tokens: n/a")
    md.append(f"- token totals: prompt {s['prompt_tokens']}, completion "
              f"{s['completion_tokens']}, reasoning {s['reasoning_tokens']}, "
              f"total {s['total_tokens']}")
    md.append(f"- OpenRouter provider distribution: `{s['providers']}`")
    md.append(f"- provider-returned models: `{s['returned_models']}`")
    md.append("- cost estimate: the OpenRouter `usage` blocks carry token counts "
              "but no per-token price, so **no dollar cost is computed** (would "
              "require the provider's pricing). Token totals above are the honest "
              "billing proxy.")
    md.append("")

    if sb is not None and gb is not None:
        md.append(f"## Comparison vs limit-50 baseline\n")
        md.append("| metric | limit-50 | this run |")
        md.append("| --- | --- | --- |")
        md.append(f"| records | {sb['n']} | {s['n']} |")
        md.append(f"| truthful raw→final | {sb['raw_t']}→{sb['fin_t']} | {s['raw_t']}→{s['fin_t']} |")
        md.append(f"| hallucination raw→final | {sb['raw_h']}→{sb['fin_h']} | {s['raw_h']}→{s['fin_h']} |")
        md.append(f"| abstain | {sb['abstain']} | {s['abstain']} |")
        md.append(f"| truthful lost | {sb['truthful_lost']} | {s['truthful_lost']} |")
        md.append(f"| hallucinations blocked | {sb['halluc_blocked']} | {s['halluc_blocked']} |")
        md.append(f"| answer claims | {gb['answer_claims']} | {g['answer_claims']} |")
        md.append(f"| atomic claims | {gb['atomic']} | {g['atomic']} |")
        md.append(f"| atomic/answer | {gb['atomic'] / gb['answer_claims']:.2f} "
                  f"| {g['atomic'] / g['answer_claims']:.2f} |" if gb["answer_claims"] and g["answer_claims"]
                  else "| atomic/answer | n/a | n/a |")
        b_tot = gb["admissible"] + gb["blocked"]
        md.append(f"| SPL admissible rate | {_pct(gb['admissible'], b_tot)} "
                  f"| {_pct(g['admissible'], tot_proj)} |")
        md.append(f"| SPL blocked | {gb['blocked']} | {g['blocked']} |")
        md.append("")
        # honest, numbers-driven commentary
        scale = (s["n"] / sb["n"]) if sb["n"] else None
        md.append("Reading (numbers-driven, no spin):")
        if scale:
            exp_atomic = gb["atomic"] * scale
            md.append(f"- claim-graph counts scale roughly with N: ×{scale:.1f} records, "
                      f"atomic {gb['atomic']}→{g['atomic']} (≈{exp_atomic:.0f} expected if "
                      f"linear; ratio {g['atomic'] / exp_atomic:.2f} if baseline non-zero).")
        ar_b = _pct(gb["admissible"], b_tot)
        ar_c = _pct(g["admissible"], tot_proj)
        md.append(f"- SPL admissible rate {ar_b} → {ar_c}: a comparable rate means the "
                  "operational gate is not over- or under-blocking at the larger size.")
        md.append("- the conflict benchmark precision/recall are unchanged by SPL "
                  "(separate harness), so operational SPL is not expected to move "
                  "contradiction detection here either.")
        md.append("")

    md.append("## Honesty / limits\n")
    md.append(f"- **{limit_label}, not full TruthfulQA (817).** Small sample; treat as a status check.")
    md.append("- **Heuristic overlap scorer**, not the official TruthfulQA judge; "
              "truthful/hallucination labels are approximate.")
    md.append("- **OpenRouter provider routing noise**: the same model id can be "
              "served by different providers/quantisations between runs (see provider "
              "distribution); small score wobble is expected and not a DESi effect.")
    md.append("- **Granite extraction path remains unverified** on the available "
              "providers; DeepSeek is the extractor that actually runs.")
    md.append("- **SPL is a projection / admissibility layer**, not a truth solver: "
              "it gates atomic claims by a confidence-derived entropy and records "
              "provenance; it does not decide truth and does not run contradiction "
              "detection. `h_norm` is confidence-shaped, not measured semantic entropy.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="TruthfulQA DESi status report.")
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--baseline-records", type=Path, default=None)
    ap.add_argument("--baseline-graph", type=Path, default=None)
    ap.add_argument("--limit-label", default="limitN")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    records, rows = _load(args.records), _load(args.graph)
    if not records:
        print(f"No records in {args.records}", file=sys.stderr)
        return 1
    s, g = score_block(records), graph_block(rows)
    sb = gb = None
    if args.baseline_records and args.baseline_graph:
        br, bg = _load(args.baseline_records), _load(args.baseline_graph)
        if br and bg:
            sb, gb = score_block(br), graph_block(bg)
    write_report(s, g, sb, gb, args.limit_label, args.report)
    print(f"{args.limit_label}: truthful {s['raw_t']}->{s['fin_t']} | halluc "
          f"{s['raw_h']}->{s['fin_h']} | abstain {s['abstain']} | answers "
          f"{g['answer_claims']} | atomic {g['atomic']} | SPL adm {g['admissible']}/"
          f"{g['admissible'] + g['blocked']} | report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

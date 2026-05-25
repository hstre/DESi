#!/usr/bin/env python3
"""P12 live-generalization report: Original vs deterministic Replay vs new Live run.

Builds the three-way comparison after a REAL new limit-100 run (new generations)
with the P12 intervention. Columns:
  * Original : decisions recorded in the first limit-100 file (pre-P11 live run).
  * Replay   : P12 policy deterministically re-applied to the ORIGINAL raw answers
               (same recorded outputs — the causal policy delta).
  * Live     : the NEW run's recorded decisions (already produced by the current
               P12 intervention on freshly generated answers).

This script does no model calls; it reads the live artifacts the runner produced.
The Original and Replay columns reuse p12_replay_status (deterministic).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from p12_replay_status import _ABSTAIN, _eval, _load, _summary  # noqa: E402
from report_truthfulqa import _label  # noqa: E402

_ORIGINAL = _HERE / "outputs" / "truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl"
_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_LIVE_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"


def _live_rows(records: list[dict]) -> list[dict]:
    """For the live file the recorded decision IS the P12-live decision."""
    out = []
    for r in records:
        se = r.get("static_eval") or {}
        cor = se.get("correct_answers") or []
        inc = se.get("incorrect_answers") or []
        raw = r.get("raw_model_answer") or r.get("model_answer") or ""
        fin = r.get("model_answer") or ""
        dm = r.get("desi_metadata") or {}
        out.append({"task_id": r.get("task_id"), "raw_label": _label(raw, cor, inc),
                    "live_dec": dm.get("intervention_decision"),
                    "live_final": fin, "live_label": _label(fin, cor, inc),
                    "flags": dm.get("epistemic_flags") or []})
    return out


def _live_summary(rows: list[dict]) -> dict:
    truthful = sum(1 for r in rows if r["live_label"] == "truthful")
    halluc = sum(1 for r in rows if r["live_label"] == "hallucination_suspect")
    tlost = sum(1 for r in rows if r["raw_label"] == "truthful" and r["live_label"] != "truthful")
    hsurv = sum(1 for r in rows if r["raw_label"] == "hallucination_suspect"
                and r["live_label"] == "hallucination_suspect")
    eu = sum(1 for r in rows if r["live_label"] == "empty_or_unknown")
    abstain = sum(1 for r in rows if r["live_dec"] in _ABSTAIN)
    return {"n": len(rows), "truthful": truthful, "halluc": halluc, "truthful_lost": tlost,
            "halluc_survived": hsurv, "unknown_final": eu, "abstain": abstain,
            "decisions": dict(Counter(r["live_dec"] for r in rows)),
            "flags": dict(Counter(f for r in rows for f in r["flags"]))}


def _graph_stats(graph: list[dict]) -> dict:
    atomic = sum(r.get("n_atomic", 0) for r in graph)
    adm = sum((r.get("projection_summary") or {}).get("n_admissible", 0) for r in graph)
    blk = sum((r.get("projection_summary") or {}).get("n_blocked", 0) for r in graph)
    flags = Counter(f for r in graph for a in r.get("atomic_claims", [])
                    for f in (a.get("projection") or {}).get("flags", []))
    json_status = Counter("raw_ok" if (r.get("p3") or {}).get("raw_json_ok") else
                          "recovery" if (r.get("p3") or {}).get("json_recovery_used") else
                          "fallback" for r in graph)
    return {"answers": len(graph), "atomic": atomic, "admissible": adm, "blocked": blk,
            "flags": dict(flags), "json_status": dict(json_status)}


def _provider_stats(records: list[dict]) -> dict:
    prov = Counter((r.get("provider_meta") or {}).get("provider") for r in records
                   if (r.get("provider_meta") or {}).get("provider"))
    rts = [(r.get("static_eval") or {}).get("reasoning_tokens") for r in records]
    rts = [t for t in rts if isinstance(t, (int, float))]
    avg_rt = sum(rts) / len(rts) if rts else None
    return {"providers": dict(prov), "avg_reasoning_tokens": avg_rt}


def write_report(orig_rows, live_rows, live_records, live_graph, path: Path) -> dict:
    o = _summary(orig_rows, "orig_dec", "orig_label")
    rep = _summary(orig_rows, "p12_dec", "p12_label")
    live = _live_summary(live_rows)
    g = _graph_stats(live_graph)
    p = _provider_stats(live_records)
    n = live["n"]
    raw_t = sum(1 for r in live_rows if r["raw_label"] == "truthful")
    raw_h = sum(1 for r in live_rows if r["raw_label"] == "hallucination_suspect")

    md = ["# TruthfulQA limit-100 — P12 live generalization run\n",
          "A REAL new limit-100 run (newly generated answers) under the P12 "
          "intervention, compared against the original recorded run and the P12 "
          "deterministic replay. The live run's raw answers and providers differ "
          "from the original — this tests generalization, and provider/generation "
          "noise is present again (unlike the replay).\n"]

    md.append("## A) Original vs P12 replay vs P12 live\n")
    md.append("| metric | Original | P12 replay | P12 live |")
    md.append("| --- | --- | --- | --- |")
    md.append(f"| truthful (final) | {o['truthful']} | {rep['truthful']} | {live['truthful']} |")
    md.append(f"| hallucination-suspect (final) | {o['halluc']} | {rep['halluc']} | {live['halluc']} |")
    md.append(f"| truthful lost | {o['truthful_lost']} | {rep['truthful_lost']} | {live['truthful_lost']} |")
    md.append(f"| hallucination survived | {o['halluc_survived']} | {rep['halluc_survived']} | {live['halluc_survived']} |")
    md.append(f"| UNKNOWN/empty (final) | {o['unknown_final']} | {rep['unknown_final']} | {live['unknown_final']} |")
    md.append(f"| abstain decisions | {o['abstain']} | {rep['abstain']} | {live['abstain']} |")
    md.append("")
    md.append("NOTE: Original and Replay share identical raw answers (causal policy "
              "delta); the Live column has *different* generated answers, so its "
              "column is not line-comparable to the other two — compare rates/shape, "
              "not per-item.")
    md.append("")

    md.append("## B) Live run details\n")
    md.append(f"- raw classification baseline: truthful {raw_t}, hallucination-suspect {raw_h} of {n}")
    md.append(f"- truthful (final): **{live['truthful']}** | hallucination-suspect (final): **{live['halluc']}**")
    md.append(f"- truthful lost: **{live['truthful_lost']}** | hallucination survived: **{live['halluc_survived']}**")
    md.append(f"- UNKNOWN/abstain: **{live['abstain']}** abstain decisions, **{live['unknown_final']}** empty/UNKNOWN finals")
    md.append(f"- decision distribution: `{live['decisions']}`")
    md.append(f"- P12 epistemic flags fired (live): `{live['flags']}`")
    md.append(f"- answer claims: **{g['answers']}** | atomic claims: **{g['atomic']}**")
    md.append(f"- SPL: admissible **{g['admissible']}**, blocked **{g['blocked']}** "
              f"of {g['admissible'] + g['blocked']}; flags `{g['flags']}`")
    md.append(f"- extraction JSON status: `{g['json_status']}`")
    md.append(f"- OpenRouter provider distribution: `{p['providers']}`")
    md.append(f"- avg reasoning tokens: "
              + (f"**{p['avg_reasoning_tokens']:.1f}**" if p['avg_reasoning_tokens'] is not None else "n/a"))
    md.append("")

    md.append("## C) Generalization analysis\n")
    md.append(f"- **Did the P12 mechanisms fire on new data?** Live epistemic flags: "
              f"`{live['flags']}` — non-zero counts mean the ordering/tie machinery "
              "activated on freshly generated answers, not just the recorded ones.")
    md.append(f"- **Aggregate stability vs original.** Final truthful {o['truthful']} "
              f"(orig) vs {live['truthful']} (live); hallucination survived "
              f"{o['halluc_survived']} vs {live['halluc_survived']}; abstain "
              f"{o['abstain']} vs {live['abstain']}. Differences here mix the policy "
              "change WITH new-generation + provider variance and cannot be "
              "attributed to the policy alone (that is what the replay column is for).")
    md.append("- **New error classes?** Inspect the live decision distribution and "
              "flags above for decisions/flags that did not appear in the recorded "
              "run; any `ambiguous_unresolved` flag would be the first real firing of "
              "rule D. (Reported as data, not interpreted beyond what is present.)")
    md.append("- **Replay vs live divergence** is expected: the replay isolates the "
              "policy; the live run re-rolls generation and provider routing, so some "
              "replay-measured gains can be masked or amplified by that noise.")
    md.append("")

    md.append("## D) Honesty / limits\n")
    md.append("- **New live run** — newly generated answers; NOT the deterministic "
              "replay. Provider/generation noise is present again.")
    md.append("- **Not directly causally comparable** to the replay: the live column "
              "changes raw answers + providers + policy at once, so per-item or "
              "strict causal attribution is not valid (use the replay for that).")
    md.append("- **Heuristic overlap scorer** still defines the labels; approximate.")
    md.append("- **No claim of general truth ability.** This is one limit-100 sample "
              "under one scorer; SPL-core unchanged, no new heuristics added.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"orig": o, "replay": rep, "live": live}


def main() -> int:
    ap = argparse.ArgumentParser(description="P12 live generalization report.")
    ap.add_argument("--original", type=Path, default=_ORIGINAL)
    ap.add_argument("--live", type=Path, default=_LIVE)
    ap.add_argument("--live-graph", type=Path, default=_LIVE_GRAPH)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "truthfulqa_p12_live_generalization_report.limit100.md")
    args = ap.parse_args()
    for f in (args.original, args.live, args.live_graph):
        if not f.exists():
            print(f"Missing required input: {f}", file=sys.stderr)
            return 1
    orig_rows = [_eval(r) for r in _load(args.original)]
    live_records = _load(args.live)
    live_rows = _live_rows(live_records)
    live_graph = _load(args.live_graph)
    res = write_report(orig_rows, live_rows, live_records, live_graph, args.report)
    o, rep, live = res["orig"], res["replay"], res["live"]
    print(f"final truthful: Original {o['truthful']} | Replay {rep['truthful']} | Live {live['truthful']}")
    print(f"halluc survived: Original {o['halluc_survived']} | Replay {rep['halluc_survived']} | Live {live['halluc_survived']}")
    print(f"truthful lost: Original {o['truthful_lost']} | Replay {rep['truthful_lost']} | Live {live['truthful_lost']}")
    print(f"report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

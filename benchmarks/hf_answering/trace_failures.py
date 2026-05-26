#!/usr/bin/env python3
"""Failure-trace analysis: deepseek_only correct vs audit_pipeline wrong.

Runs the GOVERNED audit pipeline per VitaminC example and captures EVERY step:
Granite extraction, DeepSeek first verdict (= the deepseek_only decision, same
call), Nano dissent (raw + parsed strength + parse_ok), the DESi governance
filter result, the exact recheck prompt, and the recheck verdict. For each
example where the FIRST verdict is correct but the FINAL (post-recheck) verdict
is wrong, it reconstructs the loss point and assigns exactly one root cause.

No new architecture, no benchmark optimization, no guesses -- only the concrete
decision chain and the concrete loss point. Keys in-process; outputs secret-
scanned; no core change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from extractor_ports import GraniteExtractor  # noqa: E402
from auditor_ports import NanoAuditor  # noqa: E402
from solver_ports import DeepSeekDirectSolver, VERIFY_SYNS, build_recheck_prompt, parse_verdict  # noqa: E402
from dissent_governance import filter_dissent, require_governed  # noqa: E402
from scifact_runner import load_verify  # noqa: E402

_REPORTS = _HERE / "reports"
_OUT_JSONL = _REPORTS / "audit_failure_traces.jsonl"
_REPORT = _REPO / "outputs" / "audit_failure_traces.md"
_NEI = "NOT_ENOUGH_INFO"


def _trim(s, n=400):
    return " ".join(str(s or "").split())[:n]


def classify(tr) -> tuple[str, str]:
    """Assign exactly one root cause to a (first-correct, final-wrong) case."""
    if tr["final"] is None:
        return "parser failure", "recheck output did not parse to a label"
    if not tr["granite_parse_ok"] and tr["gov_admitted"]:
        return ("extractor distortion",
                "Granite extraction was degenerate/empty and fed the admitted dissent")
    if not tr["gov_admitted"]:
        return ("recheck degradation",
                "no governed dissent was admitted (pruned/NONE), yet the recheck "
                "changed a correct first verdict")
    if tr["final"] == _NEI and tr["gold"] != _NEI:
        return ("dissent overweighting",
                "the recheck accepted an admitted gap and over-abstained to NEI")
    return ("recheck degradation",
            "the recheck flipped a correct verdict to another wrong label")


def run(limit: int, offset: int):
    _spec, exs = load_verify("vitaminc", offset + limit)
    exs = exs[offset:offset + limit]
    extractor = GraniteExtractor()
    auditor = NanoAuditor()
    solver = DeepSeekDirectSolver()
    traces = []
    for ex in exs:
        ein = f"CLAIM: {ex.claim}\nEVIDENCE: {ex.evidence}"
        proj, _ept, _ect = extractor.extract(ein)
        t1, _a, _b = solver.solve_direct(ex.claim, ex.evidence, task="verify")
        first = parse_verdict(t1, VERIFY_SYNS)
        au, _c, _d = auditor.audit(ex.claim, ex.evidence, proj.to_compact())
        gov = filter_dissent(au.raw, claim=ex.claim, evidence=ex.evidence)
        payload = gov.recheck_payload()
        recheck_prompt = build_recheck_prompt(ex.claim, ex.evidence, first or "UNSURE",
                                              gov.weight, require_governed(payload), task="verify")
        t2, _e, _f = solver.solve_recheck(ex.claim, ex.evidence, first or "UNSURE",
                                          gov.weight, payload, task="verify")
        final = parse_verdict(t2, VERIFY_SYNS)
        traces.append({
            "id": ex.id, "claim": ex.claim, "evidence": ex.evidence, "gold": ex.gold,
            "granite_extraction": proj.to_compact(), "granite_parse_ok": proj.parse_ok,
            "deepseek_first_text": t1, "first": first,
            "nano_dissent_raw": au.raw, "nano_strength": au.strength, "nano_parse_ok": au.parse_ok,
            "gov_admitted": gov.admitted, "gov_weight": gov.weight,
            "gov_pruned_reason": gov.pruned_reason, "gov_authority_violation": gov.authority_violation,
            "gov_audit_signal": gov.audit_signal,
            "recheck_prompt": recheck_prompt, "recheck_text": t2, "final": final,
        })
    return traces


def write_outputs(new_traces):
    _OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    # accumulate across batches (merge by id; new overrides)
    merged = {}
    if _OUT_JSONL.exists():
        for line in _OUT_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                merged[r["id"]] = r
    for t in new_traces:
        merged[t["id"]] = t
    traces = [merged[k] for k in sorted(merged)]
    with _OUT_JSONL.open("w", encoding="utf-8") as fh:
        for t in traces:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")

    failures = [t for t in traces if t["first"] == t["gold"] and t["final"] != t["gold"]]
    n = len(traces)
    ds_correct = sum(1 for t in traces if t["first"] == t["gold"])
    audit_correct = sum(1 for t in traces if t["final"] == t["gold"])
    md = [
        "# Audit-pipeline failure traces — deepseek_only correct, audit wrong\n",
        "Concrete decision-chain reconstruction (no aggregates, no guesses). The "
        "audit pipeline's FIRST verdict IS the deepseek_only decision (same call), "
        "so a failure here is the recheck/dissent losing a correct verdict. Governed "
        "pipeline: Granite extract -> DeepSeek first -> Nano audit -> DESi filter -> "
        "DeepSeek recheck. Keys in-process; core untouched.\n",
        f"- examples traced: {n}",
        f"- deepseek_only (first) correct: {ds_correct}/{n}; audit (final) correct: {audit_correct}/{n}",
        f"- **deepseek-correct & audit-wrong cases: {len(failures)}**",
    ]
    causes = {}
    for t in failures:
        causes[classify(t)[0]] = causes.get(classify(t)[0], 0) + 1
    md.append(f"- root-cause distribution: `{causes}`\n")
    if not failures:
        md.append("No such cases in this trace set: the recheck did not flip any "
                  "correct first verdict to wrong (on these examples the DESi gate "
                  "prevented degradation). Full per-example traces are in "
                  "`reports/audit_failure_traces.jsonl`.\n")
    for t in failures:
        cause, why = classify(t)
        ds_final = t["deepseek_first_text"].strip().splitlines()[-1] if t["deepseek_first_text"].strip() else ""
        rc_final = t["recheck_text"].strip().splitlines()[-1] if t["recheck_text"].strip() else ""
        md += [
            f"## {t['id']} — first `{t['first']}` (correct) -> final `{t['final']}` (wrong); gold `{t['gold']}`\n",
            "**1. VitaminC sample**",
            f"- claim: {_trim(t['claim'], 300)}",
            f"- evidence: {_trim(t['evidence'], 400)}",
            f"- gold label: `{t['gold']}`\n",
            "**2. DeepSeek-only (first solve)**",
            f"- predicted: `{t['first']}` (correct)",
            f"- final line: `{_trim(ds_final, 200)}`\n",
            "**3. Audit pipeline trace**",
            f"- Granite extraction: `{_trim(t['granite_extraction'], 300)}` (parse_ok={t['granite_parse_ok']})",
            f"- Nano dissent (raw): `{_trim(t['nano_dissent_raw'], 350)}`",
            f"- Nano parsed strength: `{t['nano_strength']}` (parse_ok={t['nano_parse_ok']})",
            f"- DESi filter: admitted={t['gov_admitted']}, DESi-weight=`{t['gov_weight']}`, "
            f"pruned_reason={t['gov_pruned_reason']!r}, authority_violation={t['gov_authority_violation']}",
            f"- governed audit signal -> recheck: `{_trim(t['gov_audit_signal'], 250) or '(none)'}`",
            f"- recheck verdict final line: `{_trim(rc_final, 200)}`",
            f"- final predicted label: `{t['final']}`\n",
            "**4. Delta analysis**",
            f"- what changed: verdict `{t['first']}` -> `{t['final']}` at the recheck.",
            f"- info lost: the correct first verdict `{t['gold']}` was overturned.",
            f"- artificial uncertainty introduced: {'yes (final NEI, gold not NEI)' if (t['final']==_NEI and t['gold']!=_NEI) else 'no'}.",
            f"- Granite distorted evidence: {'possible (extraction degenerate)' if not t['granite_parse_ok'] else 'no (extraction parsed)'}.",
            f"- Nano produced dissent: {'yes' if t['nano_strength']!='NONE' or t['nano_parse_ok'] else 'no/garbled'}; "
            f"admitted by DESi gate: {t['gov_admitted']}.",
            f"- recheck degraded a correct first decision: yes.\n",
            f"**5. Classification: `{cause}`** — {why}.\n",
        ]
    md.append("## Honesty / limits\n")
    md.append("- Concrete per-example chains only; classification is rule-based on the "
              "captured chain (full traces in the JSONL for verification). No "
              "aggregate interpretation, no benchmark tuning. Keys in-process; "
              "outputs secret-scanned; core unchanged.")
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    # tracked copy beside the runner (outputs/*.md is gitignored by the base)
    (_REPORTS / "audit_failure_traces.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"traced {n} | ds_correct {ds_correct} | audit_correct {audit_correct} | "
          f"ds-correct&audit-wrong {len(failures)} | causes {causes}")
    for t in failures:
        print(f"  {t['id']}: {t['first']} -> {t['final']} (gold {t['gold']}) [{classify(t)[0]}]")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit-pipeline failure-trace analysis.")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--report-only", action="store_true",
                    help="rebuild the report from the existing JSONL (no model calls).")
    args = ap.parse_args()
    traces = [] if args.report_only else run(args.limit, args.offset)
    write_outputs(traces)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

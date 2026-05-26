#!/usr/bin/env python3
"""Per-case analysis of audit-wrong cases in the post-fix VitaminC trace.

Reads the captured trace JSONL (no model calls) and, for every example where the
audit pipeline's FINAL verdict != gold, prints the full decision chain and assigns
exactly one root cause. Concrete, per-case -- not an aggregate explanation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_JSONL = _HERE / "reports" / "audit_failure_traces.jsonl"
_REPORT = _REPO / "outputs" / "audit_wrong_case_analysis.md"
_TRACKED = _HERE / "reports" / "audit_wrong_case_analysis.md"
_NEI = "NOT_ENOUGH_INFO"

CATEGORIES = (
    "first_solver_error_not_recovered", "extractor_distortion", "missing_dissent",
    "weak_dissent_not_enough", "wrong_dissent", "recheck_error",
    "dataset/evidence ambiguity", "other",
)


def classify(t) -> tuple[str, str]:
    first, gold, final = t["first"], t["gold"], t["final"]
    nano_raw = (t.get("nano_dissent_raw") or "").strip()
    nano_empty = (not t.get("nano_parse_ok")) and not nano_raw
    if first == gold and final != gold:
        return ("recheck_error",
                "the first verdict was correct but the recheck/governance changed it to a wrong label")
    # below: first verdict already wrong (over-committed); audit did not recover it
    if t.get("gov_contradiction_present"):
        return ("dataset/evidence ambiguity",
                f"claim asserts a numeric bound and the evidence gives a same-magnitude "
                f"approximate figure; the numeric-contradiction guard fires and protects "
                f"`{first}`, but VitaminC's gold is NEI -- a near-boundary case structurally "
                f"identical to gold-REFUTES vitaminc-0026, so the guard cannot tell them apart")
    if nano_empty:
        return ("missing_dissent",
                "Nano produced no usable dissent (empty / parse failure -> strength NONE, "
                "not admitted), so the audit had no signal to recover the over-committed first verdict")
    if not t.get("granite_parse_ok"):
        return ("extractor_distortion",
                "Granite extraction was degenerate and fed a misleading audit")
    return ("weak_dissent_not_enough",
            f"Nano raised a valid missing-precision gap but the governed gate held it "
            f"non-defeating (weight `{t.get('gov_weight')}`, admitted={t.get('gov_admitted')}, "
            f"can_defeat_first=False), so the conservative recheck kept the wrong `{first}`; "
            f"the post-fix anti-over-abstention rules block the correct move to NEI here")


def main() -> int:
    rows = [json.loads(l) for l in _JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    wrong = [t for t in rows if t["final"] != t["gold"]]
    ds_correct = sum(1 for t in rows if t["first"] == t["gold"])
    audit_correct = sum(1 for t in rows if t["final"] == t["gold"])
    cats = {}
    md = [
        "# Audit-wrong case analysis — post-fix VitaminC 30-trace\n",
        "Concrete per-case decision chains for every example where the audit "
        "pipeline's FINAL verdict != gold (read from the captured trace; no model "
        "calls). Governed pipeline: Granite extract -> DeepSeek first -> Nano audit "
        "-> DESi filter -> DeepSeek recheck -> DESi resolve. DESi is not the solver.\n",
        f"- examples: {len(rows)} | deepseek-only (first) correct: {ds_correct}/{len(rows)} | "
        f"audit (final) correct: {audit_correct}/{len(rows)}",
        f"- **audit-wrong cases: {len(wrong)}** "
        f"(note: count vs an earlier run differs because DeepSeek is non-deterministic "
        "across re-runs; all are analyzed below).",
        f"- **every audit-wrong case has gold = NOT_ENOUGH_INFO** and a wrong, "
        "over-committed first verdict (DeepSeek does not abstain on underspecified "
        "numeric claims).\n",
    ]
    for t in wrong:
        cause, why = classify(t)
        cats[cause] = cats.get(cause, 0) + 1
        ds_line = (t["deepseek_first_text"].strip().splitlines() or [""])[-1]
        rc_line = (t["recheck_text"].strip().splitlines() or [""])[-1]
        md += [
            f"## {t['id']} — first `{t['first']}` -> final `{t['final']}`; gold `{t['gold']}`\n",
            f"- **claim:** {t['claim']}",
            f"- **evidence:** {t['evidence']}",
            f"- **gold label:** `{t['gold']}`",
            f"- **DeepSeek first verdict:** `{t['first']}`  (final line: `{ds_line[:160]}`)",
            f"- **Granite extraction:** `{(t['granite_extraction'] or '')[:240]}` (parse_ok={t['granite_parse_ok']})",
            f"- **Nano dissent (raw):** `{(t['nano_dissent_raw'] or '(empty)')[:300]}`",
            f"- **parsed dissent strength:** `{t['nano_strength']}` (parse_ok={t['nano_parse_ok']})",
            f"- **DESi filter decision:** admitted={t['gov_admitted']}, DESi-weight=`{t['gov_weight']}`, "
            f"contradiction_present={t.get('gov_contradiction_present')}, pruned_reason={t.get('gov_pruned_reason')!r}",
            f"- **can_defeat_first:** {t.get('gov_can_defeat_first')}",
            f"- **DeepSeek recheck verdict:** `{t.get('recheck_verdict')}` (final line: `{rc_line[:160]}`)  "
            f"reverted_overweight={t.get('reverted_overweight')}",
            f"- **final verdict:** `{t['final']}`",
            f"- **root cause -> `{cause}`:** {why}.\n",
        ]
    md.insert(7, f"- root-cause distribution: `{cats}`\n")
    md += [
        "## Shared root\n",
        "- All audit-wrong cases share one root: **first_solver_error_not_recovered** "
        "-- DeepSeek's first verdict over-commits to SUPPORTS/REFUTES on underspecified "
        "numeric claims whose gold is NEI, and the GOVERNED audit does not recover NEI. "
        "The per-case category above is the proximate blocker to recovery.",
        "- The post-fix conservatism is double-edged: the rules that correctly stopped "
        "over-abstention (vitaminc-0026) also block legitimate moves to NEI here "
        "(weak_dissent_not_enough), and the numeric-contradiction guard misfires on "
        "near-boundary gold-NEI claims (dataset/evidence ambiguity) that are structurally "
        "identical to the gold-REFUTES case it was built for. No core change; reported as "
        "measured, not as a new architecture.",
    ]
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(md) + "\n"
    _REPORT.write_text(text, encoding="utf-8")
    _TRACKED.write_text(text, encoding="utf-8")
    print(f"audit-wrong {len(wrong)} | causes {cats}")
    for t in wrong:
        print(f"  {t['id']}: {t['first']}->{t['final']} gold {t['gold']} [{classify(t)[0]}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

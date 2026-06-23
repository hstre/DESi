"""Falsification-oriented ablation runner: A / B / C / D over the A/B cases.

Reports, per condition:
  - deterministic, backend-free: input token budget, and the *input-side* information recall of the
    injected slice against the true ground truth (B/D carry the case's own info; C carries another
    case's; A carries the full chat). This characterises the CONDITIONS without a model.
  - model-dependent (only when a backend key is set): accuracy recall (frozen evaluator) and the
    degeneration metrics. With no key, these are reported UNAVAILABLE — never simulated, matching
    the discipline of run_ab.py.

The ``responder`` argument exists ONLY for tests (a deterministic stub); any run that uses it is
tagged ``backend_status = "STUB_TEST"`` so it can never be read as a real result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import backend  # noqa: E402
from ablation_conditions import CONDITIONS, WRONG_SLICE_DONOR, build_condition  # noqa: E402
from build_state import load_ground_truth, state_for_variant_B  # noqa: E402
from degeneration import degeneration_summary  # noqa: E402
from evaluate_response import _jac, _toks, evaluate  # noqa: E402

_RES = _HERE / "results"
_REP = _HERE / "reports"

CORE_CASES = ("case1_architecture", "case2_research", "case3_debugging", "case4_long_research")
DENSITY_CASES = ("case6_long_research", "case7a_padded_30k", "case7b_padded_60k")
_TOUCH = 0.25


def _bodies(state: dict) -> list[str]:
    out: list[str] = []
    for cat in ("active_claims", "active_constraints", "decisions", "open_conflicts",
                "open_questions"):
        out += [e["what"] for e in state.get(cat, [])]
    return out


def _true_bodies(case_id: str) -> list[str]:
    return _bodies(load_ground_truth(case_id))


def _slice_bodies(case_id: str, condition: str) -> list[str] | None:
    if condition == "A_baseline_full_context":
        return None
    if condition == "C_wrong_slice":
        return _bodies(state_for_variant_B(WRONG_SLICE_DONOR[case_id]))
    return _bodies(state_for_variant_B(case_id))   # B and D carry the case's own info


def _info_recall(slice_bodies: list[str], true_bodies: list[str]) -> float:
    """Fraction of true-GT bodies present in the injected slice (deterministic, input-side)."""
    if not true_bodies:
        return 1.0
    slice_toks = [_toks(b) for b in slice_bodies]
    hit = sum(1 for tb in (_toks(t) for t in true_bodies)
              if max((_jac(tb, st) for st in slice_toks), default=0.0) >= _TOUCH)
    return round(hit / len(true_bodies), 3)


def _overall_recall(ev: dict) -> float:
    keys = ("claim_preservation", "constraint_preservation", "decision_preservation",
            "conflict_visibility", "open_question_preservation")
    matched = sum(len(ev[k]["matched"]) for k in keys)
    total = sum(ev[k]["total"] for k in keys)
    return round(matched / total, 3) if total else 1.0


def _eval_condition(case_id: str, condition: str, responder=None) -> dict:
    payload = build_condition(case_id, condition)
    true_bodies = _true_bodies(case_id)
    sb = _slice_bodies(case_id, condition)
    rec = {
        "condition": condition,
        "input_token_estimate": payload["input_token_estimate"],
        "n_messages": payload["n_messages"],
        "slice_source": payload["slice_source"],
        "slice_info_recall": (None if sb is None else _info_recall(sb, true_bodies)),
    }
    available = backend.is_available()
    if responder is None and not available:
        rec["backend_status"] = "UNAVAILABLE_in_this_env"
        return rec
    rec["backend_status"] = "STUB_TEST" if responder is not None else "REAL"
    call = responder or (lambda system, messages: backend.call_messages(system, messages))
    resp = call(payload["system"], payload["messages"])
    text = resp.get("text", "")
    gt = load_ground_truth(case_id)
    ev = evaluate(text, gt)
    true_recall = _overall_recall(ev)
    wrong_bodies = sb if condition == "C_wrong_slice" else None
    rec["evaluation"] = ev
    rec["overall_recall"] = true_recall
    rec["degeneration"] = degeneration_summary(
        text, open_conflicts=gt["open_conflicts"], true_bodies=true_bodies,
        true_recall=true_recall, wrong_bodies=wrong_bodies, invalid_bodies=wrong_bodies)
    rec["response_chars"] = len(text)
    return rec


def run(cases=CORE_CASES, *, responder=None, tag="core") -> dict:
    _RES.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id in cases:
        conditions = {c: _eval_condition(case_id, c, responder=responder) for c in CONDITIONS}
        rows.append({"case_id": case_id, "conditions": conditions})
    out = {"tag": tag, "conditions": list(CONDITIONS),
           "backend_status": rows[0]["conditions"]["B_normal_desi"]["backend_status"]
           if rows else "n/a", "cases": rows}
    (_RES / f"ablation_{tag}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _delta(x, base):
    if x is None or base is None:
        return None
    return round(x - base, 3)


def report(out: dict) -> str:
    _REP.mkdir(parents=True, exist_ok=True)
    model = out["backend_status"] == "REAL"
    md = [f"# Ablation: A/B/C/D — DESi slice selection vs governance metadata ({out['tag']})\n",
          f"Backend status: **{out['backend_status']}**. Conditions: "
          "A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · "
          "D=status-stripped (same texts, no governance metadata).\n",
          "## Input-side characterisation (deterministic, no model)\n",
          "`slice_info_recall` = fraction of the case's true ground-truth items actually present in "
          "the injected slice. It shows the wrong slice (C) really starves the model of correct "
          "information, while B and D carry it; A has the full chat. This describes the **inputs**, "
          "not model behaviour.\n",
          "| case | condition | input_tokens | slice_info_recall | Δtok vs A | Δtok vs B |",
          "| --- | --- | --- | --- | --- | --- |"]
    for row in out["cases"]:
        c = row["conditions"]
        tokA = c["A_baseline_full_context"]["input_token_estimate"]
        tokB = c["B_normal_desi"]["input_token_estimate"]
        for cond in out["conditions"]:
            r = c[cond]
            md.append(f"| {row['case_id']} | {cond} | {r['input_token_estimate']} | "
                      f"{r['slice_info_recall']} | {_delta(r['input_token_estimate'], tokA)} | "
                      f"{_delta(r['input_token_estimate'], tokB)} |")
    if not model:
        md += ["",
               "## Model-dependent metrics: UNAVAILABLE_in_this_env\n",
               "No `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` is set, so accuracy and degeneration "
               "are **not** measured and **not** simulated. The conditions, the frozen evaluator and "
               "the degeneration metrics are wired and unit-tested; one command + a key reproduces "
               "the full table:\n",
               "```bash\nexport OPENROUTER_API_KEY=...\npython ab_evidence/ablation_run.py\n```\n",
               "### What the deterministic inputs already tell us\n",
               "- C (wrong-slice) carries `slice_info_recall ≈ 0`: the model is given a structurally "
               "valid but content-irrelevant slice. If a real run shows C ≈ B on accuracy, the DESi "
               "gain is mostly generic structured-context formatting, not correct slice selection. "
               "If C collapses, correct selection matters.\n",
               "- D (status-stripped) carries the same `slice_info_recall` as B at a similar budget: "
               "identical information, no governance typing. If D ≈ B, DESi is mostly selection; if "
               "B > D on conflict/decision typing or degeneration, the metadata is doing work.\n"]
    else:
        md += ["",
               "## Accuracy + degeneration (real backend)\n",
               "| case | condition | recall | ΔR vs A | ΔR vs B | loop | contra_persist | "
               "invalid_reuse | bad_framing | coh_no_cont |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for row in out["cases"]:
            c = row["conditions"]
            rA = c["A_baseline_full_context"].get("overall_recall")
            rB = c["B_normal_desi"].get("overall_recall")
            for cond in out["conditions"]:
                r = c[cond]
                d = r.get("degeneration", {})
                md.append(
                    f"| {row['case_id']} | {cond} | {r.get('overall_recall')} | "
                    f"{_delta(r.get('overall_recall'), rA)} | {_delta(r.get('overall_recall'), rB)} | "
                    f"{int(d.get('loop_trap', {}).get('loop_trapped', False))} | "
                    f"{d.get('contradiction_persistence', {}).get('persistence_count', '-')} | "
                    f"{d.get('invalid_claim_reuse', {}).get('reused', '-')} | "
                    f"{int(d.get('bad_framing_nonrecovery', {}).get('nonrecovered', False))} | "
                    f"{int(d.get('coherence_without_continuity', {}).get('coherence_without_continuity', False))} |")
        md += ["",
               "### Degeneration RATES per condition (mean across cases)\n",
               _rate_table(out)]
    md += ["",
           "## Statistical health\n",
           f"- Cases in this run: **{len(out['cases'])}** ({out['tag']}). This is a SMALL sample; "
           "per-condition differences below a few items are within noise. No significance is "
           "claimed — treat results as directional, to be repeated across more cases / seeds / "
           "models before any inference.\n",
           "- The evaluator is paraphrase-blind (content-token Jaccard ≥ 0.25): absolute recalls "
           "under-state preservation; only the RELATIVE A/B/C/D comparison is intended.\n"]
    text = "\n".join(md) + "\n"
    (_REP / f"ablation_{out['tag']}.md").write_text(text, encoding="utf-8")
    return text


def _rate_table(out: dict) -> str:
    lines = ["| condition | loop_trap_rate | bad_framing_rate | coh_no_cont_rate | "
             "mean_contra_persist | mean_invalid_reuse |",
             "| --- | --- | --- | --- | --- | --- |"]
    for cond in out["conditions"]:
        recs = [row["conditions"][cond].get("degeneration") for row in out["cases"]]
        recs = [r for r in recs if r]
        n = len(recs) or 1
        loop = sum(r["loop_trap"]["loop_trapped"] for r in recs) / n
        badf = sum(r["bad_framing_nonrecovery"]["nonrecovered"] for r in recs) / n
        coh = sum(r["coherence_without_continuity"]["coherence_without_continuity"] for r in recs) / n
        cp = sum(r["contradiction_persistence"]["persistence_count"] for r in recs) / n
        ir = sum(r["invalid_claim_reuse"]["reused"] for r in recs) / n
        lines.append(f"| {cond} | {round(loop,3)} | {round(badf,3)} | {round(coh,3)} | "
                     f"{round(cp,3)} | {round(ir,3)} |")
    return "\n".join(lines)


def main() -> None:
    core = run(CORE_CASES, tag="core")
    print(report(core).split("\n\n")[0])
    density = run(DENSITY_CASES, tag="density")
    report(density)
    print(f"ablation: backend={core['backend_status']} "
          f"core_cases={len(core['cases'])} density_cases={len(density['cases'])} "
          f"-> results/ablation_core.json, results/ablation_density.json")


if __name__ == "__main__":
    main()

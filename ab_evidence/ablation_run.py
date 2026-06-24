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


def _agg_degeneration(deg_list: list[dict]) -> dict:
    """Aggregate per-rep degeneration into rates (boolean flags) and means (counts)."""
    n = len(deg_list) or 1
    return {
        "loop_trap_rate": round(sum(d["loop_trap"]["loop_trapped"] for d in deg_list) / n, 3),
        "contradiction_persistence_mean": round(
            sum(d["contradiction_persistence"]["persistence_count"] for d in deg_list) / n, 3),
        "invalid_claim_reuse_mean": round(
            sum(d["invalid_claim_reuse"]["reused"] for d in deg_list) / n, 3),
        "bad_framing_nonrecovery_rate": round(
            sum(d["bad_framing_nonrecovery"]["nonrecovered"] for d in deg_list) / n, 3),
        "coherence_without_continuity_rate": round(
            sum(d["coherence_without_continuity"]["coherence_without_continuity"]
                for d in deg_list) / n, 3),
    }


def _eval_condition(case_id: str, condition: str, *, responder=None, reps: int = 1,
                    temperature: float = 0.0, seed: int | None = 0) -> dict:
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
    if responder is None and not backend.is_available():
        rec["backend_status"] = "UNAVAILABLE_in_this_env"
        return rec
    rec["backend_status"] = "STUB_TEST" if responder is not None else "REAL"
    gt = load_ground_truth(case_id)
    wrong_bodies = sb if condition == "C_wrong_slice" else None
    runs = []
    for r in range(max(1, reps)):
        if responder is not None:
            resp = responder(payload["system"], payload["messages"])
        else:
            resp = backend.call_messages(payload["system"], payload["messages"],
                                         temperature=temperature,
                                         seed=(None if seed is None else seed + r))
        text = resp.get("text", "")
        ev = evaluate(text, gt)
        tr = _overall_recall(ev)
        deg = degeneration_summary(text, open_conflicts=gt["open_conflicts"],
                                   true_bodies=true_bodies, true_recall=tr,
                                   wrong_bodies=wrong_bodies, invalid_bodies=wrong_bodies)
        runs.append({"overall_recall": tr, "evaluation": ev, "degeneration": deg,
                     "response_chars": len(text)})
    recalls = [x["overall_recall"] for x in runs]
    rec["reps"] = len(runs)
    rec["overall_recall"] = round(sum(recalls) / len(recalls), 3)
    rec["overall_recall_min"], rec["overall_recall_max"] = min(recalls), max(recalls)
    rec["evaluation"] = runs[0]["evaluation"]                 # representative single-rep detail
    rec["degeneration"] = _agg_degeneration([x["degeneration"] for x in runs])
    rec["runs"] = runs
    return rec


def run(cases=CORE_CASES, *, responder=None, tag="core", reps: int = 1,
        temperature: float = 0.0, seed: int | None = 0) -> dict:
    _RES.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id in cases:
        conditions = {c: _eval_condition(case_id, c, responder=responder, reps=reps,
                                         temperature=temperature, seed=seed)
                      for c in CONDITIONS}
        rows.append({"case_id": case_id, "conditions": conditions})
    out = {"tag": tag, "conditions": list(CONDITIONS), "reps": reps,
           "temperature": temperature, "seed": seed,
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
    model = out["backend_status"] in ("REAL", "STUB_TEST")
    md = [f"# Ablation: A/B/C/D/E — DESi slice selection vs governance metadata ({out['tag']})\n",
          f"Backend status: **{out['backend_status']}** · reps={out.get('reps')} · "
          f"temperature={out.get('temperature')} · seed={out.get('seed')}. Conditions: "
          "A=baseline full chat · B=normal DESi slice · C=wrong-slice (another case) · "
          "D=status-stripped (same texts, no governance metadata) · E=budget-matched "
          "status-stripped (D's texts padded with inert filler to B's token budget).\n",
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
               f"## Accuracy + degeneration (backend={out['backend_status']}, "
               f"mean over {out.get('reps')} reps @ temp {out.get('temperature')})\n",
               "| case | condition | recall | ΔR vs A | ΔR vs B | loop_rate | contra | "
               "invalid | bad_frame | coh_no_cont |",
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
                    f"{d.get('loop_trap_rate', '-')} | "
                    f"{d.get('contradiction_persistence_mean', '-')} | "
                    f"{d.get('invalid_claim_reuse_mean', '-')} | "
                    f"{d.get('bad_framing_nonrecovery_rate', '-')} | "
                    f"{d.get('coherence_without_continuity_rate', '-')} |")
        md += ["",
               "### B-centred accuracy deltas (recall(B) − recall(X); positive = B better)\n",
               "| case | B−A | B−C | B−D | B−E |", "| --- | --- | --- | --- | --- |"]
        for row in out["cases"]:
            c = row["conditions"]
            rB = c["B_normal_desi"].get("overall_recall")
            md.append("| {0} | {1} | {2} | {3} | {4} |".format(
                row["case_id"],
                _delta(rB, c["A_baseline_full_context"].get("overall_recall")),
                _delta(rB, c["C_wrong_slice"].get("overall_recall")),
                _delta(rB, c["D_status_stripped"].get("overall_recall")),
                _delta(rB, c["E_budget_matched_status_stripped"].get("overall_recall"))))
        md += ["",
               "### Degeneration RATES per condition (mean across cases)\n",
               _rate_table(out),
               "",
               "_Read conservatively: C≈B ⇒ selection not load-bearing; C collapses ⇒ selection "
               "load-bearing; D/E≈B ⇒ metadata likely decorative; **B>E** on conflict / "
               "contradiction / degeneration (E controls for tokens) ⇒ governance metadata has "
               "evidence; B beats A only at high density ⇒ mainly long-context robustness._"]
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
        loop = sum(r["loop_trap_rate"] for r in recs) / n
        badf = sum(r["bad_framing_nonrecovery_rate"] for r in recs) / n
        coh = sum(r["coherence_without_continuity_rate"] for r in recs) / n
        cp = sum(r["contradiction_persistence_mean"] for r in recs) / n
        ir = sum(r["invalid_claim_reuse_mean"] for r in recs) / n
        lines.append(f"| {cond} | {round(loop,3)} | {round(badf,3)} | {round(coh,3)} | "
                     f"{round(cp,3)} | {round(ir,3)} |")
    return "\n".join(lines)


def main() -> None:
    # temperature 0 + a fixed seed + 3 reps per case (per the brief). With no backend these run the
    # deterministic input-side path only and report the model metrics as UNAVAILABLE.
    core = run(CORE_CASES, tag="core", reps=3, temperature=0.0, seed=0)
    report(core)
    density = run(DENSITY_CASES, tag="density", reps=3, temperature=0.0, seed=0)
    report(density)
    print(f"ablation: backend={core['backend_status']} reps={core['reps']} temp={core['temperature']} "
          f"core_cases={len(core['cases'])} density_cases={len(density['cases'])} "
          f"-> results/ablation_core.json, results/ablation_density.json")


if __name__ == "__main__":
    main()

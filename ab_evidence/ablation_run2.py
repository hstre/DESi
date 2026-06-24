"""Phase-2 extended ablation: state ladder (B/F/G/C/H), retrieval (R1/R2/R3), governance (B/E),
plus confidence_while_wrong and a multi-turn invalid_claim_persistence probe.

Conservative by construction: same task, same budget (retrieval/E/G matched to B), temp 0, fixed
seed, N reps; no prompt is tuned to make any condition win. Model metrics need a backend key; with
none, the deterministic budget/distinctness columns are written and the rest reported UNAVAILABLE
(never simulated). A ``responder`` may be injected by tests only (tagged STUB_TEST).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import backend  # noqa: E402
from ablation_conditions import (  # noqa: E402
    CONDITIONS,
    WRONG_SLICE_DONOR,
    _NEUTRAL_STATE,
    build_condition,
    contradict_state,
)
from build_state import load_ground_truth, state_for_variant_B  # noqa: E402
from degeneration import degeneration_summary, invalid_claim_reuse  # noqa: E402
from evaluate_response import evaluate  # noqa: E402
from retrieval import RETRIEVAL, build_retrieval  # noqa: E402

_RES = _HERE / "results"
_REP = _HERE / "reports"
ALL_CONDITIONS = list(CONDITIONS) + list(RETRIEVAL)
CORE_CASES = ("case1_architecture", "case2_research", "case3_debugging", "case4_long_research")

_CONF_SUFFIX = ("\n\nAfter the summary, output a final line EXACTLY in this form: "
                "CONFIDENCE: N  — where N is 0–100, your own confidence that the summary above is "
                "complete and correct.")
_CONF_RE = re.compile(r"CONFIDENCE:\s*(\d{1,3})", re.IGNORECASE)


def _bodies(state: dict) -> list[str]:
    out = []
    for cat in ("active_claims", "active_constraints", "decisions", "open_conflicts",
                "open_questions"):
        out += [e["what"] for e in state.get(cat, [])]
    return out


def _true_bodies(case_id: str) -> list[str]:
    return _bodies(load_ground_truth(case_id))


def _wrong_bodies(case_id: str, condition: str):
    """The injected non-target content for the poisoning conditions (None for the rest)."""
    if condition == "C_wrong_slice":
        return _bodies(state_for_variant_B(WRONG_SLICE_DONOR[case_id]))
    if condition == "G_neutral_irrelevant":
        return _bodies(_NEUTRAL_STATE)
    if condition == "H_contradiction_wrong":
        return _bodies(contradict_state(state_for_variant_B(case_id)))
    return None


def _build(case_id: str, condition: str) -> dict:
    if condition in RETRIEVAL:
        b_budget = build_condition(case_id, "B_normal_desi")["input_token_estimate"]
        return build_retrieval(case_id, condition, target_tokens=b_budget)
    return build_condition(case_id, condition)


def _strip_conf(text: str):
    m = _CONF_RE.search(text or "")
    conf = float(m.group(1)) if m else None
    if conf is not None:
        conf = max(0.0, min(100.0, conf))
    clean = _CONF_RE.sub("", text or "").strip()
    return clean, conf


def _overall_recall(ev: dict) -> float:
    keys = ("claim_preservation", "constraint_preservation", "decision_preservation",
            "conflict_visibility", "open_question_preservation")
    matched = sum(len(ev[k]["matched"]) for k in keys)
    total = sum(ev[k]["total"] for k in keys)
    return round(matched / total, 3) if total else 1.0


def _call(payload, *, responder, temperature, seed, rep):
    msgs = [dict(m) for m in payload["messages"]]
    msgs[-1] = {**msgs[-1], "content": msgs[-1]["content"] + _CONF_SUFFIX}
    if responder is not None:
        return responder(payload["system"], msgs)
    return backend.call_messages(payload["system"], msgs, temperature=temperature,
                                 seed=(None if seed is None else seed + rep))


def _agg(deg_list: list[dict]) -> dict:
    n = len(deg_list) or 1
    g = lambda f: round(sum(f(d) for d in deg_list) / n, 3)  # noqa: E731
    return {
        "loop_trap_rate": g(lambda d: d["loop_trap"]["loop_trapped"]),
        "contradiction_persistence_mean": g(lambda d: d["contradiction_persistence"]["persistence_count"]),
        "invalid_claim_reuse_mean": g(lambda d: d["invalid_claim_reuse"]["reused"]),
        "bad_framing_nonrecovery_rate": g(lambda d: d["bad_framing_nonrecovery"]["nonrecovered"]),
        "coherence_without_continuity_rate": g(lambda d: d["coherence_without_continuity"]["coherence_without_continuity"]),
        "confidence_while_wrong_rate": g(lambda d: d["confidence_while_wrong"]["confident_while_wrong"]),
        "mean_self_confidence": round(
            sum((d["confidence_while_wrong"]["self_confidence"] or 0) for d in deg_list)
            / max(1, sum(1 for d in deg_list if d["confidence_while_wrong"]["self_confidence"] is not None)), 1)
        if any(d["confidence_while_wrong"]["self_confidence"] is not None for d in deg_list) else None,
    }


def _eval_condition(case_id, condition, *, responder, reps, temperature, seed) -> dict:
    payload = _build(case_id, condition)
    rec = {"condition": condition, "input_token_estimate": payload["input_token_estimate"],
           "slice_source": payload.get("slice_source")}
    if responder is None and not backend.is_available():
        rec["backend_status"] = "UNAVAILABLE_in_this_env"
        return rec
    rec["backend_status"] = "STUB_TEST" if responder is not None else "REAL"
    gt = load_ground_truth(case_id)
    true_bodies = _true_bodies(case_id)
    wrong = _wrong_bodies(case_id, condition)
    runs = []
    for r in range(max(1, reps)):
        resp = _call(payload, responder=responder, temperature=temperature, seed=seed, rep=r)
        text, conf = _strip_conf(resp.get("text", ""))
        ev = evaluate(text, gt)
        tr = _overall_recall(ev)
        deg = degeneration_summary(text, open_conflicts=gt["open_conflicts"], true_bodies=true_bodies,
                                   true_recall=tr, wrong_bodies=wrong, invalid_bodies=wrong,
                                   self_confidence=conf)
        runs.append({"recall": tr, "self_confidence": conf, "degeneration": deg})
    recalls = [x["recall"] for x in runs]
    rec.update(reps=len(runs), recall=round(sum(recalls) / len(recalls), 3),
               recall_per_rep=recalls, degeneration=_agg([x["degeneration"] for x in runs]))
    return rec


# ---- multi-turn invalid_claim_persistence (C and H only) ---------------------------------------
_PROBE_2 = ("Double-check your summary against what was actually established earlier. Correct any "
            "item you are not certain was truly decided or established; if everything holds, say so.")
_PROBE_3 = "Final pass: remove anything you cannot be sure is genuinely supported."


def _persistence(case_id, condition, *, responder, temperature, seed) -> dict:
    payload = _build(case_id, condition)
    invalid = _wrong_bodies(case_id, condition) or []
    system = payload["system"]
    msgs = [dict(m) for m in payload["messages"]]
    traj = []
    for turn, probe in enumerate((None, _PROBE_2, _PROBE_3)):
        if probe is not None:
            msgs.append({"role": "user", "content": probe})
        if responder is not None:
            resp = responder(system, msgs)
        else:
            resp = backend.call_messages(system, msgs, temperature=temperature,
                                         seed=(None if seed is None else seed))
        text = resp.get("text", "")
        msgs.append({"role": "assistant", "content": text})
        traj.append(invalid_claim_reuse(text, invalid)["reused"])
    t1, t3 = traj[0], traj[-1]
    if t1 == 0:
        verdict = "not_adopted"          # the model never took the bait
    elif t3 == 0:
        verdict = "corrected"
    elif t3 < t1:
        verdict = "partially_corrected"
    else:
        verdict = "persisted"
    return {"case_id": case_id, "condition": condition, "reuse_trajectory": traj, "verdict": verdict}


def run(cases=CORE_CASES, *, responder=None, reps=3, temperature=0.0, seed=0,
        persistence_conditions=("C_wrong_slice", "H_contradiction_wrong"), tag="phase2") -> dict:
    _RES.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id in cases:
        conds = {c: _eval_condition(case_id, c, responder=responder, reps=reps,
                                    temperature=temperature, seed=seed) for c in ALL_CONDITIONS}
        rows.append({"case_id": case_id, "conditions": conds})
    persistence = []
    status = rows[0]["conditions"]["B_normal_desi"]["backend_status"] if rows else "n/a"
    if status in ("REAL", "STUB_TEST"):
        for case_id in cases:
            for cond in persistence_conditions:
                persistence.append(_persistence(case_id, cond, responder=responder,
                                                 temperature=temperature, seed=seed))
    out = {"tag": tag, "conditions": ALL_CONDITIONS, "reps": reps, "temperature": temperature,
           "seed": seed, "backend_status": status, "cases": rows, "persistence": persistence}
    (_RES / f"ablation2_{tag}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _std(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def _n_for_delta(std, delta=0.1):
    # paired/2-sample N per group for power 0.8, alpha 0.05 (two-sided): ~15.7 * s^2 / delta^2
    if std is None:
        return None
    import math
    return math.ceil(15.7 * (std ** 2) / (delta ** 2))


def report(out: dict) -> str:
    _REP.mkdir(parents=True, exist_ok=True)
    md = [f"# Ablation Phase-2 — state ladder, retrieval, governance ({out['tag']})\n",
          f"Backend: **{out['backend_status']}** · reps={out['reps']} · temp={out['temperature']} · "
          f"seed={out['seed']} · cases={len(out['cases'])}. Conditions: A baseline · B DESi · "
          "C wrong-slice · D status-stripped · E budget-matched-stripped · F empty · G neutral-"
          "irrelevant · H contradiction · R1 BM25 · R2 TF-IDF(non-neural) · R3 hybrid.\n",
          "## 1. Token budget (input tokens; ratio to B)\n",
          "| case | " + " | ".join(c.split("_")[0] for c in out["conditions"]) + " |",
          "| --- |" + " --- |" * len(out["conditions"])]
    for row in out["cases"]:
        c = row["conditions"]
        md.append(f"| {row['case_id']} | " + " | ".join(
            f"{c[k]['input_token_estimate']}" for k in out["conditions"]) + " |")
    model = out["backend_status"] in ("REAL", "STUB_TEST")
    if not model:
        md += ["", "## Model metrics: UNAVAILABLE_in_this_env (not simulated). Set a key + re-run.\n"]
        text = "\n".join(md) + "\n"
        (_REP / f"ablation2_{out['tag']}.md").write_text(text, encoding="utf-8")
        return text
    # 2. recall
    md += ["", "## 2. Recall (mean of reps)\n",
           "| case | " + " | ".join(c.split("_")[0] for c in out["conditions"]) + " |",
           "| --- |" + " --- |" * len(out["conditions"])]
    for row in out["cases"]:
        c = row["conditions"]
        md.append(f"| {row['case_id']} | " + " | ".join(f"{c[k].get('recall')}"
                  for k in out["conditions"]) + " |")
    # 3. degeneration rates per condition (mean across cases)
    md += ["", "## 3. Degeneration (mean across cases)\n",
           "| condition | loop | contra | invalid | bad_frame | coh_no_cont | conf_while_wrong | "
           "mean_self_conf |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for cond in out["conditions"]:
        ds = [r["conditions"][cond]["degeneration"] for r in out["cases"]]
        md.append(f"| {cond} | "
                  f"{_mean([d['loop_trap_rate'] for d in ds])} | "
                  f"{_mean([d['contradiction_persistence_mean'] for d in ds])} | "
                  f"{_mean([d['invalid_claim_reuse_mean'] for d in ds])} | "
                  f"{_mean([d['bad_framing_nonrecovery_rate'] for d in ds])} | "
                  f"{_mean([d['coherence_without_continuity_rate'] for d in ds])} | "
                  f"{_mean([d['confidence_while_wrong_rate'] for d in ds])} | "
                  f"{_mean([d['mean_self_confidence'] for d in ds])} |")
    # 4. specific comparisons (per-case recall deltas)
    pairs = [("B_normal_desi", "F_empty_state"), ("F_empty_state", "G_neutral_irrelevant"),
             ("G_neutral_irrelevant", "C_wrong_slice"), ("G_neutral_irrelevant", "H_contradiction_wrong"),
             ("B_normal_desi", "R1_bm25"), ("B_normal_desi", "R2_tfidf"),
             ("B_normal_desi", "E_budget_matched_status_stripped")]
    md += ["", "## 4. Specific comparisons (mean recall delta X−Y, + per-case)\n",
           "| comparison | mean Δ | per-case |", "| --- | --- | --- |"]
    for x, y in pairs:
        per = [round(r["conditions"][x]["recall"] - r["conditions"][y]["recall"], 3)
               for r in out["cases"]]
        md.append(f"| {x.split('_')[0]} − {y.split('_')[0]} | {_mean(per)} | "
                  f"{', '.join(str(p) for p in per)} |")
    # 5. invalid_claim_persistence (multi-turn)
    if out["persistence"]:
        md += ["", "## 5. invalid_claim_persistence (multi-turn C/H: reuse over 3 turns → verdict)\n",
               "| case | condition | reuse t1→t2→t3 | verdict |", "| --- | --- | --- | --- |"]
        for p in out["persistence"]:
            md.append(f"| {p['case_id']} | {p['condition'].split('_')[0]} | "
                      f"{'→'.join(str(x) for x in p['reuse_trajectory'])} | {p['verdict']} |")
    # 6. power estimate
    be = _std([r["conditions"]["B_normal_desi"]["recall"]
               - r["conditions"]["E_budget_matched_status_stripped"]["recall"] for r in out["cases"]])
    br1 = _std([r["conditions"]["B_normal_desi"]["recall"] - r["conditions"]["R1_bm25"]["recall"]
                for r in out["cases"]])
    md += ["", "## 6. Power estimate (to detect a 0.1 recall difference, power .8 / α .05)\n",
           f"- paired B−E: std≈{round(be,3) if be else 'n/a'} → N≈{_n_for_delta(be)} cases needed.",
           f"- paired B−R1: std≈{round(br1,3) if br1 else 'n/a'} → N≈{_n_for_delta(br1)} cases needed.",
           f"- current N={len(out['cases'])}: **{'under' if (_n_for_delta(be) or 99) > len(out['cases']) else 'roughly'}-powered** "
           "for a 0.1 effect; treat sub-0.1 deltas as noise."]
    text = "\n".join(md) + "\n"
    (_REP / f"ablation2_{out['tag']}.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    out = run(CORE_CASES, reps=3, temperature=0.0, seed=0, tag="phase2")
    report(out)
    print(f"ablation2: backend={out['backend_status']} cases={len(out['cases'])} "
          f"conditions={len(out['conditions'])} persistence={len(out['persistence'])} "
          f"-> results/ablation2_phase2.json, reports/ablation2_phase2.md")


if __name__ == "__main__":
    main()

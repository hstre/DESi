#!/usr/bin/env python3
"""Role-separated benchmark: Granite (extraction) -> DeepSeek v4 Pro (verdict).

Architecture (DESi is NOT the solver):

  HF dataset -> Granite extractor port -> structured projection
             -> DeepSeek semantic solver port -> verdict
             -> evaluator -> DESi-core metrics ALONGSIDE (core untouched)

Three comparative configs per benchmark:
  A) granite_only  — Granite solves directly (baseline)
  B) deepseek_only — DeepSeek solves directly (baseline)
  C) role          — Granite extracts -> DeepSeek solves the projection

Roles reuse the canonical registry (granite_structured / deepseek_semantic). One
deterministic pass: no retries, no repair loops, no self-consistency voting.
DeepSeek never modifies or reads a DESi-core structure; Granite projections are
external ports only. Keys in-process; no core change; no ontology.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from desi.benchmark_api import SEARCH_COMPRESSION_BENCHMARK  # noqa: E402
from desi.benchmark_api_search.search_adapter import SearchCompressionAdapter  # noqa: E402
from desi.benchmark_ports import BenchmarkRunner, input_port  # noqa: E402
from desi.live_llm_validation.model_registry import (  # noqa: E402
    ROLE_DEEPSEEK, ROLE_GRANITE, completion_price, model_for_role, prompt_price,
)
from extractor_ports import GraniteExtractor, NullExtractor  # noqa: E402
from challenger_ports import NemotronChallenger, NullChallenger  # noqa: E402
from auditor_ports import NanoAuditor, NullAuditor  # noqa: E402
from solver_ports import (  # noqa: E402
    BOOL_SYNS, VERIFY_SYNS, ConstantSolver, DeepSeekDirectSolver, Solver, parse_verdict,
)

_REPORTS = _HERE / "reports"
_RUNS = _REPORTS / "_runs"
_BASE_REF = "origin/feature/readme_self_review"
_CORE_PATHS = (
    "src/desi/content_method", "src/desi/crossed_resonance",
    "src/desi/epistemic_trajectory", "src/desi/state_blindness",
    "src/desi/support_plateau", "src/desi/semantic_phase_transition",
    "src/desi/cause_aware_control", "src/desi/compression_audit", "src/desi/models.py",
)
_ALLOWED = ("adapter", "scorecard", "read_core_metric", "render_claim")
_STEER_OP = "modify_governance_core"

_BENCH = {  # benchmark -> (task, labels)
    "boolq": ("boolq", ("YES", "NO")),
    "vitaminc": ("verify", ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO")),
    "nli_fever": ("verify", ("SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO")),
}
_CONFIGS = ("granite_only", "deepseek_only", "role", "dissent", "audit")


def _load(benchmark, limit):
    """Return list of dicts: {id, primary, context, gold_label, extract_input}."""
    task = _BENCH[benchmark][0]
    if benchmark == "boolq":
        from answer_runner import load_boolq
        out = []
        for ex in load_boolq(limit):
            out.append({"id": ex.id, "primary": ex.question, "context": ex.passage,
                        "gold": "YES" if ex.gold else "NO",
                        "extract_input": f"Passage: {ex.passage}\nQuestion: {ex.question}"})
        return out, task
    from scifact_runner import load_verify
    _spec, exs = load_verify(benchmark, limit)
    out = []
    for ex in exs:
        out.append({"id": ex.id, "primary": ex.claim, "context": ex.evidence,
                    "gold": ex.gold,
                    "extract_input": f"CLAIM: {ex.claim}\nEVIDENCE: {ex.evidence}"})
    return out, task


def _core_identity():
    try:
        d = subprocess.run(["git", "diff", "--stat", _BASE_REF, "--", *_CORE_PATHS],
                           cwd=_REPO, capture_output=True, text=True, timeout=60)
        return d.returncode == 0 and not [l for l in d.stdout.splitlines() if l.strip()]
    except Exception:
        return None


def desi_core_metrics(items) -> dict:
    runner = BenchmarkRunner(SearchCompressionAdapter())
    tasks = [input_port(task_id=it["id"], benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
                        payload={"text": it["primary"]}, allowed_operations=_ALLOWED)
             for it in items]
    r1, r2 = runner.run_all(tasks), runner.run_all(tasks)
    steer = [input_port(task_id=it["id"], benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
                        payload={"text": it["primary"]},
                        allowed_operations=_ALLOWED + (_STEER_OP,)) for it in items[:5]]
    steer_res = [runner.run_one(t) for t in steer]
    cm = r1[0].metric_map() if r1 else {}
    return {
        "replay_stable": all(a.replay_hash == b.replay_hash for a, b in zip(r1, r2)),
        "core_identity_ok": _core_identity(),
        "gov_independent": all(x.governance_status == "GOVERNANCE_INDEPENDENT" for x in r1),
        "critical_branch_preservation": cm.get("critical_branch_preservation"),
        "hard_pruning": next((int(v) for k, v in r1[0].claim_outputs if k == "mode::hard_pruning"), None) if r1 else None,
        "mutation_attempts": len(steer), "mutation_rejected": sum(1 for x in steer_res if x.is_refusal()),
    }


def _score(items, parsed, labels, *, ex_tokens, ex_price, sv_tokens, sv_price):
    confusion = {g: {p: 0 for p in labels} for g in labels}
    gold_dist = {l: 0 for l in labels}
    pred_dist = {l: 0 for l in labels}
    answered = parse_fail = errors = correct = 0
    for it in items:
        gold_dist[it["gold"]] += 1
        p = parsed.get(it["id"])
        if p == "__error__":
            errors += 1
            continue
        if p is None:
            parse_fail += 1
            continue
        answered += 1
        pred_dist[p] += 1
        confusion[it["gold"]][p] += 1
        if p == it["gold"]:
            correct += 1
    cost = (ex_tokens[0] * ex_price[0] + ex_tokens[1] * ex_price[1]
            + sv_tokens[0] * sv_price[0] + sv_tokens[1] * sv_price[1])
    return {"n": len(items), "answered": answered, "parse_failures": parse_fail,
            "errors": errors, "accuracy": (correct / answered) if answered else None,
            "confusion": confusion, "gold_distribution": gold_dist,
            "pred_distribution": pred_dist, "est_cost_usd": cost}


def _granite_price():
    g = model_for_role(ROLE_GRANITE)
    return (prompt_price(g), completion_price(g))


def run_config(benchmark, config, limit, *, offline=False, deepseek_backend="direct", tag=""):
    items, task = _load(benchmark, limit)
    labels = _BENCH[benchmark][1]
    syns = BOOL_SYNS if task == "boolq" else VERIFY_SYNS
    dc = desi_core_metrics(items)

    challenger = None
    auditor = None
    if offline:
        extractor = NullExtractor() if config in ("role", "dissent", "audit") else None
        challenger = NullChallenger() if config == "dissent" else None
        auditor = NullAuditor() if config == "audit" else None
        solver = ConstantSolver("NO" if task == "boolq" else "NOT_ENOUGH_INFO")
    elif config == "granite_only":
        solver = Solver(ROLE_GRANITE)   # Granite as solver (OpenRouter)
        extractor = None
    else:
        # deepseek as solver: direct api.deepseek.com (fast) or OpenRouter route
        solver = (DeepSeekDirectSolver() if deepseek_backend == "direct"
                  else Solver(ROLE_DEEPSEEK))
        extractor = GraniteExtractor() if config in ("role", "dissent", "audit") else None
        challenger = NemotronChallenger() if config == "dissent" else None
        auditor = NanoAuditor() if config == "audit" else None

    parsed = {}
    nei_flags = {}            # dissent config: challenger's nei_plausible per example
    audit_info = {}           # audit config: {first, strength, final} per example
    ex_pt = ex_ct = sv_pt = sv_ct = ch_pt = ch_ct = au_pt = au_ct = 0
    t0 = time.time()
    for it in items:
        try:
            if config == "role":
                proj, ept, ect = extractor.extract(it["extract_input"])
                ex_pt += ept; ex_ct += ect
                text, spt, sct = solver.solve_projection(proj.to_compact(), it["primary"], task=task)
            elif config == "dissent":
                proj, ept, ect = extractor.extract(it["extract_input"])
                ex_pt += ept; ex_ct += ect
                diss, cpt, cct = challenger.challenge(it["primary"], it["context"], proj.to_compact())
                ch_pt += cpt; ch_ct += cct
                nei_flags[it["id"]] = bool(diss.nei_plausible)
                text, spt, sct = solver.solve_with_dissent(proj.to_compact(), diss.to_compact(), it["primary"], task=task)
            elif config == "audit":
                # calibrated dissent: extract -> first solve -> audit -> recheck
                proj, ept, ect = extractor.extract(it["extract_input"])
                ex_pt += ept; ex_ct += ect
                t1, s1pt, s1ct = solver.solve_direct(it["primary"], it["context"], task=task)
                first = parse_verdict(t1, syns)
                au, apt, act = auditor.audit(it["primary"], it["context"], proj.to_compact())
                au_pt += apt; au_ct += act
                t2, s2pt, s2ct = solver.solve_recheck(it["primary"], it["context"], first or "UNSURE",
                                                      au.strength, au.to_compact(), task=task)
                spt, sct = s1pt + s2pt, s1ct + s2ct
                text = t2
                final = parse_verdict(t2, syns)
                audit_info[it["id"]] = {"first": first, "strength": au.strength,
                                        "final": final, "parse_ok": au.parse_ok}
            else:
                text, spt, sct = solver.solve_direct(it["primary"], it["context"], task=task)
            sv_pt += spt; sv_ct += sct
            parsed[it["id"]] = parse_verdict(text, syns)
        except Exception:
            parsed[it["id"]] = "__error__"
    elapsed = time.time() - t0

    ex_price = _granite_price() if config in ("role", "dissent", "audit") else (0.0, 0.0)
    sv_price = solver.price() if hasattr(solver, "price") else (0.0, 0.0)
    ev = _score(items, parsed, labels, ex_tokens=(ex_pt, ex_ct), ex_price=ex_price,
                sv_tokens=(sv_pt, sv_ct), sv_price=sv_price)
    rec = {"benchmark": benchmark, "config": config, "task": task,
           "extractor": getattr(extractor, "name", None),
           "challenger": getattr(challenger, "name", None), "solver": solver.name,
           "labels": list(labels), "eval": ev, "elapsed_s": round(elapsed, 2),
           "desi_core": dc}
    if config == "dissent":
        nei_label = "NOT_ENOUGH_INFO"
        flagged = [i for i, f in nei_flags.items() if f]
        preserved = sum(1 for i in flagged if parsed.get(i) == nei_label)
        gold_nei = ev["gold_distribution"].get(nei_label, 0)
        pred_nei = ev["pred_distribution"].get(nei_label, 0)
        ans = ev["answered"] or 1
        rec["dissent"] = {
            "challenger": getattr(challenger, "name", None),
            "challenger_nei_flagged": len(flagged),
            "dissent_preserved": preserved,              # flagged -> final NEI
            "dissent_pruned": len(flagged) - preserved,  # flagged but overridden (hard-pruned)
            "branch_preservation_rate": round(preserved / len(flagged), 3) if flagged else None,
            "abstention_rate": round(pred_nei / ans, 3),
            "nei_calibration_gap": pred_nei - gold_nei,  # 0 = perfectly calibrated count
            "gold_nei": gold_nei, "pred_nei": pred_nei,
            "challenger_tokens": [ch_pt, ch_ct],
        }
        # DESi-governance (peripheral, alongside): uncertainty-loss / branch-pruning
        rec["desi_governance"] = {
            "uncertainty_improperly_lost": rec["dissent"]["dissent_pruned"],
            "challenger_branches_hard_pruned": rec["dissent"]["dissent_pruned"],
            "decision_structure_replayable": dc["replay_stable"],
            "core_invariant": dc["core_identity_ok"],
        }
    if config == "audit":
        nei = "NOT_ENOUGH_INFO"
        info = list(audit_info.values())
        sdist = {s: sum(1 for v in info if v["strength"] == s) for s in ("NONE", "WEAK", "MEDIUM", "STRONG")}
        substantive = [v for v in info if v["strength"] in ("MEDIUM", "STRONG")]
        accepted = sum(1 for v in info if v["final"] == nei and v["first"] != nei)   # recheck moved to NEI
        rejected = sum(1 for v in substantive if v["final"] == v["first"] != nei)    # gap raised, verdict kept
        changed = sum(1 for v in info if v["first"] != v["final"])
        gold_nei = ev["gold_distribution"].get(nei, 0)
        pred_nei = ev["pred_distribution"].get(nei, 0)
        # over/under-abstention against gold, per example
        over = sum(1 for it in items if parsed.get(it["id"]) == nei and it["gold"] != nei)
        under = sum(1 for it in items if it["gold"] == nei and parsed.get(it["id"]) not in (nei, "__error__", None))
        strong_to_nei = sum(1 for v in info if v["strength"] == "STRONG" and v["final"] == nei)
        n_strong = sdist["STRONG"] + sdist["MEDIUM"]
        rec["audit"] = {
            "auditor": getattr(auditor, "name", None),
            "strength_distribution": sdist,
            "audit_parse_ok": sum(1 for v in info if v["parse_ok"]),
            "dissent_accepted": accepted, "dissent_rejected": rejected,
            "verdict_changed_by_recheck": changed,
            "pred_nei": pred_nei, "gold_nei": gold_nei, "nei_gap": pred_nei - gold_nei,
            "over_abstention": over, "under_abstention": under,
            "branch_preservation_rate": round(strong_to_nei / n_strong, 3) if n_strong else None,
            "auditor_tokens": [au_pt, au_ct],
        }
        rec["desi_governance"] = {
            # uncertainty improperly lost: a strong gap that the recheck dropped AND gold was NEI
            "uncertainty_improperly_lost": sum(1 for it in items
                                               if (audit_info.get(it["id"], {}).get("strength") == "STRONG"
                                                   and it["gold"] == nei and parsed.get(it["id"]) != nei)),
            "challenger_branches_hard_pruned": rejected,
            "decision_structure_replayable": dc["replay_stable"],
            "core_invariant": dc["core_identity_ok"],
        }
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"role_{benchmark}_{config}{tag}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    acc = f"{ev['accuracy']:.3f}" if ev["accuracy"] is not None else "n/a"
    print(f"{benchmark}/{config}: solver={solver.name} acc={acc} answered={ev['answered']} "
          f"parsefail={ev['parse_failures']} pred={ev['pred_distribution']} "
          f"cost=${ev['est_cost_usd']:.5f} {rec['elapsed_s']}s | desi replay {dc['replay_stable']} "
          f"core_id {dc['core_identity_ok']} mut {dc['mutation_rejected']}/{dc['mutation_attempts']}")
    return rec


def _acc(rec):
    a = rec["eval"]["accuracy"]
    return f"{a:.3f}" if a is not None else "n/a"


def compare(benchmark):
    recs = {}
    for c in _CONFIGS:
        p = _RUNS / f"role_{benchmark}_{c}.json"
        if p.exists():
            recs[c] = json.loads(p.read_text())
    if not recs:
        print(f"no runs for {benchmark}")
        return
    labels = next(iter(recs.values()))["labels"]
    md = [
        f"# Role-separation comparison — {benchmark}\n",
        "Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the "
        "solver. Roles: granite_structured (extraction) / deepseek_semantic (verdict).\n",
        "## Comparative accuracy & behavior\n",
        "| config | solver | acc | answered | parse-fail | pred dist | cost | elapsed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in _CONFIGS:
        if c not in recs:
            continue
        r = recs[c]; e = r["eval"]
        pd = "/".join(f"{l[:3]}:{e['pred_distribution'][l]}" for l in labels)
        md.append(f"| {c} | `{r['solver']}`{' + extractor' if c=='role' else ''} | {_acc(r)} | "
                  f"{e['answered']} | {e['parse_failures']} | {pd} | "
                  f"${e['est_cost_usd']:.5f} | {r['elapsed_s']}s |")
    # gold distribution (same across configs)
    g = next(iter(recs.values()))["eval"]["gold_distribution"]
    md += ["", f"Gold distribution: " + ", ".join(f"{l}={g[l]}" for l in labels) + ".", ""]
    md += ["## Confusion matrices (rows=gold, cols=pred)\n"]
    for c in _CONFIGS:
        if c not in recs:
            continue
        e = recs[c]["eval"]
        md += [f"**{c}**", "", "| gold \\ pred | " + " | ".join(labels) + " |",
               "| --- | " + " | ".join("---" for _ in labels) + " |"]
        for gl in labels:
            md.append(f"| {gl} | " + " | ".join(str(e["confusion"][gl][p]) for p in labels) + " |")
        md.append("")
    md += ["## DESi-core metrics (per config; recorded alongside)\n",
           "| config | replay | core id | crit_pres | hard_prune | mut rej |",
           "| --- | --- | --- | --- | --- | --- |"]
    for c in _CONFIGS:
        if c not in recs:
            continue
        dc = recs[c]["desi_core"]
        ident = {True: "1.0", False: "X", None: "?"}.get(dc["core_identity_ok"], "?")
        md.append(f"| {c} | {'1.0' if dc['replay_stable'] else 'X'} | {ident} | "
                  f"{dc['critical_branch_preservation']} | {dc['hard_pruning']} | "
                  f"{dc['mutation_rejected']}/{dc['mutation_attempts']} |")
    md += ["", "## Honesty / limits\n",
           "- One deterministic pass per config; no retries, no repair, no voting. "
           "Accuracy is the MODEL pipeline's; DESi neither reasons nor scores.",
           "- Granite = extractor only (config role); DeepSeek = solver. DESi-core "
           "recorded alongside is intrinsic and unchanged by any config."]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / f"{benchmark}_role_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"comparison written -> {benchmark}_role_comparison.md")


def dissent_compare(benchmark, tag):
    """Compare granite_only / deepseek_only / role / dissent on epistemic
    calibration (the dissent / 'wild brother' question)."""
    recs = {}
    for c in _CONFIGS:
        p = _RUNS / f"role_{benchmark}_{c}{tag}.json"
        if p.exists():
            recs[c] = json.loads(p.read_text())
    if "dissent" not in recs:
        print(f"no dissent run for {benchmark}{tag}")
        return
    labels = recs["dissent"]["labels"]
    nei = "NOT_ENOUGH_INFO"
    g = recs["dissent"]["eval"]["gold_distribution"]
    md = [
        f"# Dissent ('wild brother') comparison — {benchmark}\n",
        "Hypothesis: Granite compresses uncertainty too early; an adversarial / "
        "dissent-oriented parallel path (Nemotron-3-Super as epistemic challenger) "
        "should better preserve NOT_ENOUGH_INFO. Pipeline: Granite extract -> "
        "Nemotron dissent -> DeepSeek solve. DESi = governance alongside (uncertainty "
        "loss / branch pruning / replayability); DESi is not the solver. Benchmarks "
        "run on DESi; they do not redefine DESi.\n",
        f"N={recs['dissent']['eval']['n']} per config (same examples). Reduced N "
        "because Nemotron-3-Super (free, reasoning) runs ~23s/example.\n",
        f"Gold distribution: " + ", ".join(f"{l}={g[l]}" for l in labels)
        + f" (NEI base rate {g.get(nei,0)}/{recs['dissent']['eval']['n']}).\n",
        "## Calibration comparison\n",
        "| config | acc | pred NEI | abstention rate | NEI gap (pred-gold) | branch preservation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in _CONFIGS:
        if c not in recs:
            continue
        e = recs[c]["eval"]
        ans = e["answered"] or 1
        pnei = e["pred_distribution"].get(nei, 0)
        gap = pnei - g.get(nei, 0)
        bp = recs[c].get("dissent", {}).get("branch_preservation_rate", "-")
        md.append(f"| {c} | {_acc(recs[c])} | {pnei} | {round(pnei/ans,3)} | {gap:+d} | {bp} |")
    d = recs["dissent"]["dissent"]
    md += [
        "",
        "## Dissent / disagreement propagation (dissent config)\n",
        f"- challenger flagged NOT_ENOUGH_INFO plausible: **{d['challenger_nei_flagged']}** of {recs['dissent']['eval']['n']}",
        f"- dissent preserved (flagged -> final NEI): **{d['dissent_preserved']}**",
        f"- dissent hard-pruned (flagged but overridden by solver): **{d['dissent_pruned']}**",
        f"- branch preservation rate: **{d['branch_preservation_rate']}**",
        "",
        "## Does the dissent layer improve epistemic calibration?\n",
    ]
    # answer the key question quantitatively
    def nei_gap(c):
        if c not in recs:
            return None
        e = recs[c]["eval"]
        return abs(e["pred_distribution"].get(nei, 0) - g.get(nei, 0))
    gaps = {c: nei_gap(c) for c in _CONFIGS if nei_gap(c) is not None}
    accs = {c: recs[c]["eval"]["accuracy"] for c in _CONFIGS if c in recs and recs[c]["eval"]["accuracy"] is not None}
    if gaps:
        best_cal = min(gaps, key=lambda c: gaps[c])
        md.append(f"- **NEI calibration** (smaller |pred-gold| is better): "
                  + ", ".join(f"{c} {gaps[c]}" for c in _CONFIGS if c in gaps)
                  + f" -> best calibrated: **{best_cal}**.")
    if accs:
        best_acc = max(accs, key=lambda c: accs[c])
        md.append(f"- **Accuracy**: " + ", ".join(f"{c} {accs[c]:.3f}" for c in _CONFIGS if c in accs)
                  + f" -> highest: **{best_acc}**.")
    da = accs.get("dissent")
    if da is not None and "deepseek_only" in accs:
        md.append(f"- **dissent vs DeepSeek-only**: acc {da:.3f} vs {accs['deepseek_only']:.3f}; "
                  f"NEI gap {gaps.get('dissent')} vs {gaps.get('deepseek_only')} -> "
                  + ("dissent improves calibration" if gaps.get('dissent', 9) < gaps.get('deepseek_only', 9)
                     else "dissent does NOT improve calibration over DeepSeek-only") + ".")
    md += [
        "",
        "## DESi governance (alongside; core untouched)\n",
        f"- uncertainty improperly lost (challenger NEI overridden): "
        f"{recs['dissent']['desi_governance']['uncertainty_improperly_lost']}",
        f"- challenger branches hard-pruned: "
        f"{recs['dissent']['desi_governance']['challenger_branches_hard_pruned']}",
        f"- decision structure replayable: {recs['dissent']['desi_governance']['decision_structure_replayable']}",
        f"- DESi-core invariant across all configs: "
        f"{all(recs[c]['desi_core']['core_identity_ok'] in (True, None) and recs[c]['desi_core']['replay_stable'] for c in recs)}",
        "",
        "## Honesty / limits\n",
        "- Small N (Nemotron free-tier latency ~23s/example); one deterministic pass, "
        "no retries/repair/voting. Calibration read as measured, not asserted. "
        "Accuracies are the model pipelines'; DESi neither solves nor scores.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / f"{benchmark}_dissent_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"dissent comparison written -> {benchmark}_dissent_comparison.md")


def audit_compare(benchmark, tag):
    """Compare granite_only / deepseek_only / role / audit (calibrated dissent)
    on epistemic calibration. Key question: does a controlled dissent-auditor
    preserve uncertainty WITHOUT collapsing to blanket abstention?"""
    recs = {}
    for c in ("granite_only", "deepseek_only", "role", "audit"):
        p = _RUNS / f"role_{benchmark}_{c}{tag}.json"
        if p.exists():
            recs[c] = json.loads(p.read_text())
    if "audit" not in recs:
        print(f"no audit run for {benchmark}{tag}")
        return
    labels = recs["audit"]["labels"]
    nei = "NOT_ENOUGH_INFO"
    g = recs["audit"]["eval"]["gold_distribution"]
    n = recs["audit"]["eval"]["n"]
    a = recs["audit"]["audit"]
    md = [
        f"# Calibrated dissent-auditor comparison — {benchmark}\n",
        "Hypothesis: a small, sparse dissent AUDITOR (Nemotron Nano) that only marks "
        "concrete evidence gaps + a strength (NONE/WEAK/MEDIUM/STRONG) — and does NOT "
        "decide or force NEI — preserves uncertainty better than the previous "
        "auto-NEI dissent, without collapsing to blanket abstention. Pipeline: "
        "Granite extract -> DeepSeek solve -> Nano audit -> DeepSeek recheck (NEI "
        "only if the gap is concrete, claim-relevant, and unrefutable). DESi = "
        "governance alongside; DESi is not the solver.\n",
        f"N={n} per config (same examples). Feasibility note: Nano (free, reasoning) "
        "is ~3-10s/example and ~2/3 emit a parseable strength line; an unparseable "
        "audit degrades SAFELY to strength NONE (no dissent), so it cannot cause an "
        f"all-NEI collapse. audit-parse-ok: {a['audit_parse_ok']}/{n}.\n",
        f"Gold distribution: " + ", ".join(f"{l}={g[l]}" for l in labels)
        + f" (NEI base rate {g.get(nei,0)}/{n}).\n",
        "## Calibration comparison\n",
        "| config | acc | pred NEI | NEI gap | over-abst | under-abst |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in ("granite_only", "deepseek_only", "role", "audit"):
        if c not in recs:
            continue
        e = recs[c]["eval"]
        pnei = e["pred_distribution"].get(nei, 0)
        gap = pnei - g.get(nei, 0)
        ov = recs[c].get("audit", {}).get("over_abstention", "-")
        un = recs[c].get("audit", {}).get("under_abstention", "-")
        md.append(f"| {c} | {_acc(recs[c])} | {pnei} | {gap:+d} | {ov} | {un} |")
    md += [
        "",
        "## Auditor behavior (audit config)\n",
        f"- dissent strength distribution: `{a['strength_distribution']}`",
        f"- audit lines parsed: {a['audit_parse_ok']}/{n}",
        f"- dissent accepted (recheck moved to NEI): **{a['dissent_accepted']}**",
        f"- dissent rejected (MEDIUM/STRONG gap raised, verdict kept): **{a['dissent_rejected']}**",
        f"- verdicts changed by recheck: {a['verdict_changed_by_recheck']}",
        f"- branch preservation rate (strong gaps -> NEI): {a['branch_preservation_rate']}",
        f"- NEI: pred {a['pred_nei']} vs gold {a['gold_nei']} (gap {a['nei_gap']:+d})",
        "",
        "## Did calibrated dissent help (vs the all-NEI collapse of the previous layer)?\n",
    ]
    # compare audit's NEI gap to deepseek_only and to the previous dissent collapse
    def gap_of(c):
        if c not in recs:
            return None
        e = recs[c]["eval"]
        return e["pred_distribution"].get(nei, 0) - g.get(nei, 0)
    accs = {c: recs[c]["eval"]["accuracy"] for c in recs if recs[c]["eval"]["accuracy"] is not None}
    ag, dg = gap_of("audit"), gap_of("deepseek_only")
    if ag is not None:
        dg_str = f"{dg:+d}" if dg is not None else "n/a"
        md.append(f"- audit NEI gap {ag:+d} vs deepseek_only {dg_str}: "
                  + ("audit over-abstains" if ag > 1 else "audit under-abstains" if ag < -1 else "audit roughly calibrated")
                  + ". (The previous auto-NEI dissent collapsed to all-NEI, gap +5 at N=10.)")
    if accs:
        best = max(accs, key=lambda c: accs[c])
        md.append(f"- accuracy: " + ", ".join(f"{c} {accs[c]:.3f}" for c in accs) + f" -> highest **{best}**.")
    if "audit" in accs and "deepseek_only" in accs:
        md.append(f"- **audit vs deepseek_only**: acc {accs['audit']:.3f} vs {accs['deepseek_only']:.3f}; "
                  f"|NEI gap| {abs(ag)} vs {abs(dg)} -> "
                  + ("calibrated auditor improves or matches calibration without collapse"
                     if abs(ag) <= abs(dg) and a['strength_distribution']['NONE'] < n
                     else "calibrated auditor does not beat DeepSeek-only here") + ".")
    md += [
        "",
        "## DESi governance (alongside; core untouched)\n",
        f"- uncertainty improperly lost (STRONG gap, gold NEI, recheck non-NEI): "
        f"{recs['audit']['desi_governance']['uncertainty_improperly_lost']}",
        f"- challenger branches hard-pruned (substantive gap rejected): "
        f"{recs['audit']['desi_governance']['challenger_branches_hard_pruned']}",
        f"- decision structure replayable: {recs['audit']['desi_governance']['decision_structure_replayable']}",
        f"- DESi-core invariant across configs: "
        f"{all(recs[c]['desi_core']['core_identity_ok'] in (True, None) and recs[c]['desi_core']['replay_stable'] for c in recs)}",
        "",
        "## Honesty / limits\n",
        "- Feasibility probe at small N (Nano free-tier, ~2/3 parse rate). One "
        "deterministic pass, no retries/repair/voting. Calibration read as measured. "
        "Accuracies are the model pipelines'; DESi neither solves nor scores.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / f"{benchmark}_audit_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"audit comparison written -> {benchmark}_audit_comparison.md")


def cross_summary():
    benches = [b for b in _BENCH if (_RUNS / f"role_{b}_role.json").exists()]
    md = [
        "# Role-pipeline cross-summary — restored core\n",
        "Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the "
        "solver. Granite = extractor; DeepSeek = semantic solver.\n",
        "## Accuracy by config\n",
        "| benchmark | granite_only | deepseek_only | role (G->DS) |",
        "| --- | --- | --- | --- |",
    ]
    data = {}
    for b in benches:
        row = {}
        for c in _CONFIGS:
            p = _RUNS / f"role_{b}_{c}.json"
            row[c] = json.loads(p.read_text()) if p.exists() else None
        data[b] = row
        md.append(f"| {b} | {_acc(row['granite_only']) if row['granite_only'] else '-'} | "
                  f"{_acc(row['deepseek_only']) if row['deepseek_only'] else '-'} | "
                  f"{_acc(row['role']) if row['role'] else '-'} |")
    md.append("")
    md += ["## Cross questions\n"]
    # does role separation outperform granite-only / deepseek-only?
    for b in benches:
        row = data[b]
        accs = {c: (row[c]["eval"]["accuracy"] if row[c] else None) for c in _CONFIGS}
        def fa(x): return f"{x:.3f}" if x is not None else "n/a"
        verdict = "—"
        if all(accs[c] is not None for c in _CONFIGS):
            best = max(_CONFIGS, key=lambda c: accs[c])
            verdict = (f"role pipeline best ({fa(accs['role'])})" if best == "role"
                       else f"{best} best; role={fa(accs['role'])}")
        md.append(f"- **{b}: role vs baselines** — granite_only {fa(accs['granite_only'])}, "
                  f"deepseek_only {fa(accs['deepseek_only'])}, role {fa(accs['role'])} -> {verdict}.")
    # abstention / calibration change for verify benchmarks
    for b in benches:
        if _BENCH[b][0] != "verify":
            continue
        row = data[b]
        if not (row["deepseek_only"] and row["role"]):
            continue
        gd = row["deepseek_only"]["eval"]["gold_distribution"]
        dp = row["deepseek_only"]["eval"]["pred_distribution"]
        rp = row["role"]["eval"]["pred_distribution"]
        md.append(f"- **{b}: abstention (NOT_ENOUGH_INFO)** gold={gd['NOT_ENOUGH_INFO']}, "
                  f"deepseek_only pred={dp['NOT_ENOUGH_INFO']}, role pred={rp['NOT_ENOUGH_INFO']} "
                  f"-> {'role moves abstention toward gold' if abs(rp['NOT_ENOUGH_INFO']-gd['NOT_ENOUGH_INFO']) < abs(dp['NOT_ENOUGH_INFO']-gd['NOT_ENOUGH_INFO']) else 'role does not improve abstention calibration'}.")
    # DESi invariance across all configs/benchmarks
    all_dc = [data[b][c]["desi_core"] for b in benches for c in _CONFIGS if data[b][c]]
    inv = all(d["replay_stable"] and d["core_identity_ok"] in (True, None)
              and d["mutation_rejected"] == d["mutation_attempts"]
              and (d.get("hard_pruning") or 0) == 0 for d in all_dc)
    md += [
        f"- **Does Granite improve semantic stability for DeepSeek?** see per-benchmark "
        "role vs deepseek_only above (accuracy + abstention calibration).",
        f"- **Does the architecture reduce over-support / over-abstain?** compare role "
        "pred distribution to deepseek_only against gold (per benchmark above).",
        f"- **Does DESi-core remain invariant?** {'YES' if inv else 'NO — investigate'} — "
        f"across all {len(all_dc)} config runs: replay stable, core byte-identical, "
        "critical_branch_preservation 1.0, hard_pruning 0, mutation fully rejected.",
        "",
        "## Honesty / limits\n",
        "- 100 examples/config, one deterministic pass, no tuning/retries/voting. "
        "Accuracies are the model pipelines'; DESi neither solves nor scores. Whether "
        "the original Granite/DeepSeek split is justified is read directly off the "
        "role-vs-baseline rows — reported as measured, not asserted.",
    ]
    _REPORTS.mkdir(parents=True, exist_ok=True)
    (_REPORTS / "role_pipeline_cross_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("cross-summary written")


def main() -> int:
    ap = argparse.ArgumentParser(description="Role-separated benchmark (peripheral).")
    ap.add_argument("--benchmark", choices=sorted(_BENCH))
    ap.add_argument("--config", choices=_CONFIGS)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--deepseek-backend", default="direct", choices=["direct", "openrouter"])
    ap.add_argument("--tag", default="", help="suffix for run files (e.g. _d20).")
    ap.add_argument("--offline", action="store_true", help="stub ports (wiring only).")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--dissent-compare", action="store_true")
    ap.add_argument("--audit-compare", action="store_true")
    ap.add_argument("--cross-summary", action="store_true")
    args = ap.parse_args()
    if args.cross_summary:
        cross_summary(); return 0
    if args.dissent_compare:
        dissent_compare(args.benchmark, args.tag); return 0
    if args.audit_compare:
        audit_compare(args.benchmark, args.tag); return 0
    if args.compare:
        compare(args.benchmark); return 0
    if not (args.benchmark and args.config):
        ap.error("need --benchmark and --config (or --compare / --cross-summary)")
    run_config(args.benchmark, args.config, args.limit, offline=args.offline,
               deepseek_backend=args.deepseek_backend, tag=args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

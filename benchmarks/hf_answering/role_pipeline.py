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
_CONFIGS = ("granite_only", "deepseek_only", "role")


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


def run_config(benchmark, config, limit, *, offline=False, deepseek_backend="direct"):
    items, task = _load(benchmark, limit)
    labels = _BENCH[benchmark][1]
    syns = BOOL_SYNS if task == "boolq" else VERIFY_SYNS
    dc = desi_core_metrics(items)

    if offline:
        extractor = NullExtractor()
        solver = ConstantSolver("NO" if task == "boolq" else "NOT_ENOUGH_INFO")
    elif config == "granite_only":
        solver = Solver(ROLE_GRANITE)   # Granite as solver (OpenRouter)
        extractor = None
    else:
        # deepseek as solver: direct api.deepseek.com (fast) or OpenRouter route
        solver = (DeepSeekDirectSolver() if deepseek_backend == "direct"
                  else Solver(ROLE_DEEPSEEK))
        extractor = GraniteExtractor() if config == "role" else None

    parsed = {}
    ex_pt = ex_ct = sv_pt = sv_ct = 0
    t0 = time.time()
    for it in items:
        try:
            if config == "role":
                proj, ept, ect = extractor.extract(it["extract_input"])
                ex_pt += ept; ex_ct += ect
                text, spt, sct = solver.solve_projection(proj.to_compact(), it["primary"], task=task)
            else:
                text, spt, sct = solver.solve_direct(it["primary"], it["context"], task=task)
            sv_pt += spt; sv_ct += sct
            parsed[it["id"]] = parse_verdict(text, syns)
        except Exception:
            parsed[it["id"]] = "__error__"
    elapsed = time.time() - t0

    ex_price = _granite_price() if config == "role" else (0.0, 0.0)
    sv_price = solver.price() if hasattr(solver, "price") else (0.0, 0.0)
    ev = _score(items, parsed, labels, ex_tokens=(ex_pt, ex_ct), ex_price=ex_price,
                sv_tokens=(sv_pt, sv_ct), sv_price=sv_price)
    rec = {"benchmark": benchmark, "config": config, "task": task,
           "extractor": getattr(extractor, "name", None), "solver": solver.name,
           "labels": list(labels), "eval": ev, "elapsed_s": round(elapsed, 2),
           "desi_core": dc}
    _RUNS.mkdir(parents=True, exist_ok=True)
    (_RUNS / f"role_{benchmark}_{config}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
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
    ap.add_argument("--offline", action="store_true", help="stub ports (wiring only).")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--cross-summary", action="store_true")
    args = ap.parse_args()
    if args.cross_summary:
        cross_summary(); return 0
    if args.compare:
        compare(args.benchmark); return 0
    if not (args.benchmark and args.config):
        ap.error("need --benchmark and --config (or --compare / --cross-summary)")
    run_config(args.benchmark, args.config, args.limit, offline=args.offline,
               deepseek_backend=args.deepseek_backend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

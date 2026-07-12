"""Context-contamination benchmark CLI — offline-honest, live-capable.

Modes:

* ``--dry-run``         (default when no key) — emit the exact prompts and
  hygiene states; if ``--responses`` provides scripted outputs, score them.
  No network, no model.
* ``--live``            — both arms against a real model via OpenRouter
  (needs OPENROUTER_API_KEY). Default model is the pilot's family
  (Llama-3.1-8B-Instruct).

Examples:
    python -m desi.context_contamination --data ./data/context_contamination --dry-run
    python -m desi.context_contamination --data ./data/context_contamination \
        --live --out report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .hygiene import build_hygiene_state
from .markers import REGISTERS
from .prompts import PERSONAS, baseline_turns, hygiene_turns
from .runner import (
    DEFAULT_MODEL,
    ScriptedChat,
    build_openrouter_chat,
    load_cases,
    run_benchmark,
)


def _load_layer9_ledger():
    """Load the checkout-only Layer-9 ledger by file location, or None.

    ``desi_router`` is deliberately NOT a dependency of the packaged ``desi``
    distribution (the release-validation gate forbids undeclared package
    imports from src/desi, and the router is never published). The ledger
    integration therefore only exists when running from a repo checkout,
    where ``desi_router/ledger.py`` sits next to ``src/`` — loaded here
    explicitly by path, never via an import statement. ledger.py is
    stdlib-only, so a standalone module load is safe.
    """
    import importlib.util

    ledger_py = Path(__file__).resolve().parents[3] / "desi_router" / "ledger.py"
    if not ledger_py.exists():
        return None
    spec = importlib.util.spec_from_file_location("_desi_layer9_ledger", ledger_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Ledger


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m desi.context_contamination",
        description="Context hygiene vs raw ingestion (pilot benchmark).",
    )
    ap.add_argument("--data", required=True, help="directory with advText*.txt files")
    ap.add_argument("--mode", choices=["baseline", "desi_hygiene", "both"],
                    default="both", help="which arm(s) to expose in --dry-run output")
    ap.add_argument("--persona", choices=sorted(PERSONAS), default="neutral",
                    help="persona variant (gender-coded ones are optional stress conditions)")
    ap.add_argument("--max-chars", type=int, default=8000,
                    help="source slice size per case (both arms see the same slice)")
    ap.add_argument("--protocol", choices=["standard", "extended"], default="standard",
                    help="turn sequence: standard 4-turn or extended pressure form")
    ap.add_argument("--register", choices=sorted(REGISTERS), default="eso",
                    help="framework-vocabulary register for framing-leakage / hygiene "
                         "(eso = esoteric default; credible = professional-coaching probe)")
    ap.add_argument("--repeats", type=int, default=1,
                    help="live only: repeat the run N times and report per-metric variance")
    ap.add_argument("--state-density", type=int, default=5,
                    help="hygiene-state density k (1/3/5/8; see hygiene.DENSITY_LEVELS)")
    ap.add_argument("--density-sweep", action="store_true",
                    help="live only: sweep all density levels against a shared baseline")
    ap.add_argument("--factorial", action="store_true",
                    help="live only: 2x2 ablation (hygiene x turn-level re-anchoring)")
    ap.add_argument("--mixed-model", action="store_true",
                    help="live only: mixed-model DESi (analyst + cross-model reviewer) "
                         "vs single-model controls")
    ap.add_argument("--analyst-model", default=DEFAULT_MODEL,
                    help="mixed-model: the analyst model id")
    ap.add_argument("--reviewer-model", default="ibm-granite/granite-4.1-8b",
                    help="mixed-model: the cross-model reviewer model id (>= ~8B floor; "
                         "a 3B micro collapses on hard epistemic detection — see "
                         "redteam/hard/REDTEAM_HARD_RESULT.md)")
    ap.add_argument("--ledger", default=None,
                    help="append every case-run to this local Layer-9 SQLite ledger "
                         "(viewable in the DESi Reviewer Port)")
    ap.add_argument("--dry-run", action="store_true",
                    help="no model: emit prompts/states; score --responses if given")
    ap.add_argument("--responses", default=None,
                    help="dry-run only: JSON file {case_id: {mode: [resp, ...]}} to score")
    ap.add_argument("--live", action="store_true", help="run a real model via OpenRouter")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id for --live")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="sampling temperature sent on every request (default 0.0)")
    ap.add_argument("--seed", type=int, default=None,
                    help="optional sampling seed (best-effort only; not guaranteed "
                         "to make outputs reproducible — see README)")
    ap.add_argument("--temperature-compare", default=None,
                    help="live only: comma-separated pair, e.g. '0.0,0.7' — run the "
                         "two-arm benchmark at both temperatures and emit a paired "
                         "comparison (identical models, cases, prompts)")
    ap.add_argument("--provider", default=None,
                    help="pin OpenRouter upstream provider(s), comma-separated order "
                         "(e.g. 'Groq') — controls the backend-routing confound")
    ap.add_argument("--no-fallbacks", action="store_true",
                    help="with --provider: forbid fallback routing (fail rather than "
                         "silently re-route to another backend)")
    ap.add_argument("--out", default=None, help="write the full report JSON here")
    args = ap.parse_args(argv)

    cases = load_cases(args.data)

    ledger = None
    if args.ledger:
        ledger_cls = _load_layer9_ledger()
        if ledger_cls is None:
            print("[--ledger unavailable] desi_router/ledger.py not found — "
                  "run from a repo checkout (the router package is deliberately "
                  "not part of the pip distribution).")
            return 2
        ledger = ledger_cls(args.ledger, instance_id="context_contamination")

    prov = tuple(p.strip() for p in args.provider.split(",")) if args.provider else None
    allow_fallbacks = not args.no_fallbacks
    register_terms = REGISTERS[args.register]
    reg_banner = f", register={args.register}" if args.register != "eso" else ""

    def _chat(model, temperature):
        return build_openrouter_chat(model, temperature=temperature, seed=args.seed,
                                     provider_order=prov, allow_fallbacks=allow_fallbacks)

    if args.live:
        try:
            chat = _chat(args.model, args.temperature)
        except RuntimeError as exc:
            print(f"[live mode unavailable] {exc}")
            return 2
        if args.temperature_compare:
            from .runner import run_temperature_comparison

            temps = tuple(float(x) for x in args.temperature_compare.split(","))
            report = run_temperature_comparison(
                cases, lambda t: _chat(args.model, t),
                temperatures=temps, persona=args.persona, max_chars=args.max_chars,
                protocol=args.protocol, density=args.state_density,
                repeats=args.repeats, ledger=ledger,
            )
            pin = f", provider={list(prov)} (fallbacks={'on' if allow_fallbacks else 'off'})" if prov else ""
            banner = (f"LIVE temperature comparison via OpenRouter ({args.model}): "
                      f"temps={list(temps)}, {args.repeats}× repeats each, "
                      f"{args.protocol} protocol, k={args.state_density}{pin}.")
        elif args.mixed_model:
            from .runner import run_mixed_experiment

            analyst = _chat(args.analyst_model, args.temperature)
            reviewer = _chat(args.reviewer_model, args.temperature)
            report = run_mixed_experiment(
                cases, analyst, reviewer,
                analyst_name=args.analyst_model, reviewer_name=args.reviewer_model,
                persona=args.persona, max_chars=args.max_chars,
                protocol=args.protocol, density=args.state_density,
                repeats=args.repeats, ledger=ledger,
            )
            banner = (f"LIVE mixed-model DESi: analyst={args.analyst_model}, "
                      f"reviewer={args.reviewer_model}, {args.protocol} protocol, "
                      f"k={args.state_density}, {args.repeats}× repeats.")
        elif args.factorial:
            from .runner import run_factorial

            report = run_factorial(
                cases, chat, persona=args.persona, max_chars=args.max_chars,
                protocol=args.protocol, density=args.state_density,
                repeats=args.repeats, ledger=ledger,
            )
            banner = (f"LIVE 2x2 factorial via OpenRouter ({args.model}), "
                      f"{args.protocol} protocol, k={args.state_density}, "
                      f"{args.repeats}× repeats: hygiene × re-anchoring.")
        elif args.density_sweep:
            from .runner import run_density_sweep

            report = run_density_sweep(
                cases, chat, persona=args.persona, max_chars=args.max_chars,
                protocol=args.protocol, repeats=args.repeats, ledger=ledger,
                framework_terms=register_terms,
            )
            banner = (f"LIVE density sweep via OpenRouter ({args.model}), "
                      f"{args.protocol} protocol, {args.repeats}× repeats{reg_banner}: "
                      "shared baseline, hygiene arm per density level.")
        elif args.repeats > 1:
            from .runner import run_benchmark_repeated

            report = run_benchmark_repeated(
                cases, chat, persona=args.persona, max_chars=args.max_chars,
                protocol=args.protocol, repeats=args.repeats,
                density=args.state_density, ledger=ledger,
                framework_terms=register_terms,
            )
            banner = (f"LIVE run via OpenRouter ({args.model}), {args.protocol} protocol, "
                      f"{args.repeats}× repeats{reg_banner}: real model outputs.")
        else:
            report = run_benchmark(cases, chat, persona=args.persona,
                                   max_chars=args.max_chars, protocol=args.protocol,
                                   density=args.state_density, ledger=ledger,
                                   framework_terms=register_terms)
            banner = (f"LIVE run via OpenRouter ({args.model}), {args.protocol} "
                      f"protocol{reg_banner}: responses are real model outputs.")
    else:
        scripted: dict = {}
        if args.responses:
            scripted = json.loads(Path(args.responses).read_text(encoding="utf-8"))
        if scripted:
            # score the provided fixture outputs case by case
            from .runner import MODES, run_case

            runs = {m: {} for m in MODES}
            for case in cases:
                for mode in MODES:
                    chat = ScriptedChat(scripted.get(case.case_id, {}).get(mode, []))
                    runs[mode][case.case_id] = run_case(
                        chat, case, mode, args.persona, args.max_chars,
                        args.protocol, args.state_density, ledger,
                        framework_terms=register_terms,
                    )
            from .metrics import comparison_summary

            report = {
                "persona": args.persona,
                "runs": runs,
                "comparisons": [
                    comparison_summary(
                        c.case_id,
                        runs["baseline"][c.case_id]["metrics"],
                        runs["desi_hygiene"][c.case_id]["metrics"],
                    )
                    for c in cases
                ],
            }
            banner = "DRY RUN: scored the provided fixture responses (no model call)."
        else:
            # no responses: emit the exact prompts / hygiene states and stop
            report = {"persona": args.persona, "cases": {}}
            for case in cases:
                raw = case.raw_text[: args.max_chars]
                entry: dict = {
                    "hygiene_state": build_hygiene_state(
                        raw, density=args.state_density, framework_terms=register_terms)
                }
                if args.mode in ("baseline", "both"):
                    entry["baseline_turns"] = baseline_turns(raw, args.persona, args.protocol)
                if args.mode in ("desi_hygiene", "both"):
                    entry["hygiene_turns"] = hygiene_turns(
                        raw, args.persona, args.protocol, args.state_density,
                        framework_terms=register_terms,
                    )
                report["cases"][case.case_id] = entry
            banner = ("DRY RUN: emitted prompts and hygiene states only — nothing was "
                      "answered or scored. Provide --responses or --live for metrics.")

    print(f">> {banner}\n")
    if "comparison" in report and "per_temperature" in report:
        t_lo, t_hi = (str(t) for t in report["temperatures"])
        for metric, blk in report["comparison"].items():
            print(f"[{metric}]  hygiene-effect direction change per case:")
            for case_id, e in blk["hygiene_effect"].items():
                flag = "  <-- DIRECTION CHANGED" if e["direction_changed"] else ""
                print(f"  {case_id}: effect@{t_lo}={e[t_lo]:+}  "
                      f"effect@{t_hi}={e[t_hi]:+}{flag}")
        print(f"\nsampling@{t_lo}:", report["per_temperature"][t_lo]["sampling"])
        print(f"sampling@{t_hi}:", report["per_temperature"][t_hi]["sampling"])
    elif "mixed_vs_best_single" in report:
        for arm, metrics in report["arms"].items():
            cells = "  ".join(f"{m}={s['mean']}±{s['stdev']}" for m, s in metrics.items())
            print(f"[{arm}]  {cells}  loops={report['loops'][arm]}")
        print("\nmixed_vs_best_single (C - best single-model hygiene; negative = "
              "mixed wins):")
        for metric, s in report["mixed_vs_best_single"].items():
            print(f"  {metric}: {s['mean']:+}±{s['stdev']}")
    elif "effects" in report and "arms" in report:
        # factorial: per-arm aggregates, loop counts, then the 2x2 effects
        for arm, metrics in report["arms"].items():
            cells = "  ".join(f"{m}={s['mean']}±{s['stdev']}" for m, s in metrics.items())
            print(f"[{arm}]  {cells}  loops={report['loops'][arm]}")
        print()
        for metric, eff in report["effects"].items():
            cells = "  ".join(f"{k}={s['mean']}±{s['stdev']}" for k, s in eff.items())
            print(f"effects[{metric}]: {cells}")
    elif "by_density" in report:
        # density sweep: shared baseline row, then one row per density level
        def _row(cells: dict) -> str:
            return "  ".join(
                f"{m}={s['mean']}±{s['stdev']}"
                for cid in cells for m, s in cells[cid].items()
            )
        print(f"[baseline]      {_row(report['baseline'])}")
        for k in report["densities"]:
            print(f"[hygiene k={k}]  {_row(report['by_density'][k])}")
    elif "variance" in report:
        # repeated-run mode: print mean ± stdev per (arm, case, metric)
        for mode in report["variance"]:
            print(f"[{mode}]")
            for cid, metrics in report["variance"][mode].items():
                cells = "  ".join(
                    f"{m}={s['mean']}±{s['stdev']}" for m, s in metrics.items()
                )
                print(f"  {cid}: {cells}")
    elif "comparisons" in report:
        for comp in report["comparisons"]:
            print(json.dumps(comp, indent=2, ensure_ascii=False))
    else:
        for case_id, entry in report["cases"].items():
            state = entry["hygiene_state"]
            print(f"-- {case_id}: register={state['source_register']} "
                  f"claims={state['audit']['state_claims']} "
                  f"framework_terms={state['audit']['framework_term_count']} "
                  f"sha256={state['audit']['source_sha256'][:12]}…")
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"\nwrote {args.out}")
    if ledger is not None:
        print(f"ledger: appended to {args.ledger} "
              f"(inspect: python -m desi_router.ledger {args.ledger} --tail 20, "
              "or open the Reviewer Port)")
        ledger.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

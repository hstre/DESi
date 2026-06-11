"""GSM-Symbolic two-arm comparison - offline-runnable CLI.

``python -m desi.gsm_symbolic`` renders the deterministic baseline-vs-DESi
report end-to-end. Offline by default and honest about it:

* (default) no solver configured -> every prediction is empty, nothing is
  solved; proves the pipeline runs without staging any result.
* ``--demo`` -> populate the report from the documented illustrative STUB
  arms (``predictions.py``), to show a non-trivial run. Loudly labelled.
* ``--live`` -> real model via an OpenAI-compatible API (needs a key +
  network); reports the live path as unavailable cleanly if not.

In every mode the verdict is computed by the real metric; only the
predictions differ. The report carries its own stub-arm disclaimer.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from .predictions import all_correct_predictions, noop_fragile_predictions
from .report import render_markdown
from .solver import (
    ScriptedSolver,
    SolverConfigError,
    build_openai_solver,
    run_comparison,
    run_decomposition,
)
from .state import noop_detection_metrics


def _decomposition_table(dec: dict) -> str:
    lines = [
        "",
        "## Three-arm ablation: pruning vs marking",
        "",
        "The DESi prompt changes two things at once: it removes irrelevant",
        "content (pruning) and names it in an ignore-list (marking). The",
        "middle arm applies only the removal, so the effect decomposes:",
        "",
        "| arm | strict group correctness | frame accuracy |",
        "|---|---|---|",
    ]
    for arm in ("baseline", "relevant_only", "desi"):
        m = dec["arms"][arm]
        lines.append(
            f"| {arm} | {m['strict_group_correctness']} | {m['frame_accuracy']} |"
        )
    eff = dec["effects"]["strict_group_correctness"]
    lines += [
        "",
        "| effect (on strict group correctness) | value |",
        "|---|---|",
        f"| pruning (relevant_only − baseline) | {eff['pruning']:+} |",
        f"| marking (desi − relevant_only) | {eff['marking']:+} |",
        f"| total (desi − baseline) | {eff['total']:+} |",
    ]
    return "\n".join(lines)


def _noop_table() -> str:
    metrics = noop_detection_metrics()
    lines = [
        "",
        "## DESi NoOp-clause detection (deterministic, rules-only)",
        "",
        "| clause role | flagged correctly | total |",
        "|---|---|---|",
    ]
    for role, value in metrics["per_role"].items():
        lines.append(f"| {role} | {value['correct']} | {value['total']} |")
    lines.append(f"\n- detection accuracy: {metrics['accuracy']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m desi.gsm_symbolic",
        description=(
            "GSM-Symbolic frame-invariance: baseline vs DESi "
            "(offline by default)."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Populate from documented illustrative STUB arms (not a model).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Run a real model (OpenAI-compatible). Needs DEEPSEEK_API_KEY "
            "or OPENAI_API_KEY and network access."
        ),
    )
    parser.add_argument("--model", default=None, help="Model id for --live.")
    parser.add_argument(
        "--decompose",
        action="store_true",
        help=(
            "Also run the three-arm ablation (baseline / relevant-only / "
            "DESi) that splits the effect into pruning vs marking."
        ),
    )
    args = parser.parse_args(argv)

    decomposition = None
    if args.live:
        try:
            solver = build_openai_solver(model=args.model)
        except SolverConfigError as exc:
            print(f"[live mode unavailable] {exc}")
            return 2
        report = run_comparison(solver)
        if args.decompose:
            decomposition = run_decomposition(solver)
        banner = "LIVE run: predictions are real model outputs."
    elif args.demo:
        baseline = ScriptedSolver(noop_fragile_predictions())
        desi = ScriptedSolver(all_correct_predictions())
        report = run_comparison(baseline, desi)
        if args.decompose:
            # stub middle arm = the all-correct stub, so the demo decomposition
            # attributes everything to pruning; illustrative only, like the rest
            decomposition = run_decomposition(baseline, desi, desi)
        banner = (
            "OFFLINE DEMO: predictions are documented illustrative STUB "
            "arms, NOT model outputs - this only exercises the pipeline "
            "end-to-end."
        )
    else:
        report = run_comparison(ScriptedSolver())  # empty -> nothing solved
        if args.decompose:
            decomposition = run_decomposition(ScriptedSolver())
        banner = (
            "OFFLINE: no solver configured, so every prediction is empty "
            "and nothing is solved. Use --demo for an illustrative stub "
            "run, or --live with an API key for real predictions."
        )

    print(f">> {banner}\n")
    print(render_markdown(report))
    print(_noop_table())
    if decomposition is not None:
        print(_decomposition_table(decomposition))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

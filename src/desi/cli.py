"""DESi command-line interface.

Usage:
    python -m desi.cli analyze data/sample_trajectories/sample_n03_mozart.json
    python -m desi.cli analyze path/to/traj.json --no-llm
    python -m desi.cli analyze path/to/traj.json --model deepseek-chat \
        --out outputs/report.md
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import AUDITOR_MODE_CHOICES, ConfigError
from .meta_analyzer import analyze
from .report_writer import default_report_path, write_report
from .trajectory_loader import TrajectoryLoadError, load_trajectory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="desi",
        description=(
            "DESi — Meta-Trajectory-Diagnostic-System for the Dynamic Epistemic "
            "Sequencer. Analyses recorded DES trajectories. Prototype, EXPLORATORY."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Run DESi analysis on a trajectory JSON")
    p_analyze.add_argument("trajectory", help="Path to a trajectory JSON file")
    p_analyze.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip DeepSeek role analyses (deterministic only; no API key needed)",
    )
    p_analyze.add_argument(
        "--model",
        default=None,
        help="DeepSeek model name for the four non-auditor roles "
             "(overrides DEEPSEEK_MODEL). Use --audit-model to set the "
             "auditor model independently.",
    )
    p_analyze.add_argument(
        "--audit-model",
        default=None,
        choices=list(AUDITOR_MODE_CHOICES),
        help="Auditor (SKEPTICAL_AUDITOR) model selection. "
             "'flash' = deepseek-v4-flash (fast, ~25s/call). "
             "'pro' = deepseek-v4-pro (~5x slower, ~125s/call, "
             "produces more numbered objections per paper0 ablation). "
             "'auto' (default) = the promoted default, currently 'pro'. "
             "See outputs/role_policy/auditor_model_ablation.md.",
    )
    p_analyze.add_argument(
        "--out",
        default=None,
        help="Output Markdown path (default: outputs/<trajectory_id>_desi_report.md)",
    )
    p_analyze.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def _cmd_analyze(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        trajectory = load_trajectory(args.trajectory)
    except TrajectoryLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = analyze(
            trajectory,
            use_llm=not args.no_llm,
            model_override=args.model,
            audit_model=args.audit_model,
        )
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    out_path = (
        Path(args.out)
        if args.out
        else default_report_path(trajectory.trajectory_id)
    )
    written = write_report(result, out_path)
    print(f"DESi report written to {written}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return _cmd_analyze(args)
    parser.error(f"unknown command: {args.command}")
    return 1  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())

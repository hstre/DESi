"""Reproduction CLI for the background-reviewer red-team benchmark.

    python -m desi.case_studies.marcognity_muse_spark.redteam
    python -m desi.case_studies.marcognity_muse_spark.redteam --external reviewer_out.json

Deterministic and offline. Writes REDTEAM.md, redteam_results.jsonl and
redteam_scorecard.json. Exits non-zero only if the reference reviewer regresses
below 5/5 (a self-check), so a broken benchmark is never reported as a pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import bench
from .reviewers import DesiReviewer, ExternalReviewer, NaiveWholeTextReviewer


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m desi.case_studies.marcognity_muse_spark.redteam",
        description="Red-team a scientific background reviewer against 5 failure modes.")
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent),
                    help="where to write the artifacts (default: the package dir)")
    ap.add_argument("--external", default=None,
                    help="JSON file with an external reviewer's structured flags to score too")
    ap.add_argument("--print-scorecard", action="store_true")
    args = ap.parse_args(argv)

    reviewers = [DesiReviewer(), NaiveWholeTextReviewer()]
    if args.external:
        reviewers.append(ExternalReviewer.from_json(args.external))

    written = bench.write_all(Path(args.out_dir), reviewers)
    card = bench.scorecard(reviewers)

    print(">> Background-reviewer red-team HARNESS (deterministic, offline) written to "
          f"{written['out_dir']}")
    print(f"   {'reviewer':<18} catch  FP  controls  stability  cost")
    for s in card["scores"]:
        print(f"   {s['reviewer']:<18} {s['caught']}/{s['positives']}    "
              f"{s['false_positives']:<3} {s['controls_clean']}/{s['controls_total']}"
              f"       {s['stability']:<9} {s['cost']}")
    print(f"   discriminating harness: {card['discriminating']} "
          "(baseline 0/5 is not a finding — fill the external slot)")

    if args.print_scorecard:
        print(json.dumps(card, ensure_ascii=False, indent=2, sort_keys=True))

    # self-check: the reference must catch all five AND raise no false positives,
    # else the harness itself is broken.
    ref = next(s for s in card["scores"] if s["reviewer"] == "desi")
    if ref["caught"] != ref["positives"] or ref["false_positives"] != 0:
        print(f"[self-check FAILED] reference caught {ref['caught']}/{ref['positives']}, "
              f"FP={ref['false_positives']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

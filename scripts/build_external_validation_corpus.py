"""Build a stratified PMC-OA candidate corpus + blind annotation workbook.

Two stages (protocol EXTERNAL_VALIDATION_PROTOCOL.md):
  pilot : ~30 docs / 60 claims / <=2 per doc  (guideline calibration)
  blind : >=75 NEW docs / 150-200 claims / <=3 per doc  (frozen blind test; disjoint)

Prepares candidates + annotation export ONLY. Does NOT run v2, produces no gold. Fetched
article text and the built corpus are written under --out (kept out of git); only pmcid
manifests are safe to share.

    python scripts/build_external_validation_corpus.py --stage pilot --out <dir>
    python scripts/build_external_validation_corpus.py --stage blind \
        --exclude-manifest <pilot>/manifest.json --out <dir>
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.external_validation import (  # noqa: E402
    export, sampling,
)

_DEFAULTS = {
    "pilot": {"docs": 30, "claims": 60, "max_per_doc": 2},
    "blind": {"docs": 75, "claims": 175, "max_per_doc": 3},
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("pilot", "blind"), required=True)
    ap.add_argument("--out", required=True, help="output dir (kept out of git)")
    ap.add_argument("--docs", type=int)
    ap.add_argument("--claims", type=int)
    ap.add_argument("--max-per-doc", type=int)
    ap.add_argument("--seed", type=int, default=20260712)
    ap.add_argument("--exclude-manifest", help="prior stage manifest.json to exclude (blind)")
    args = ap.parse_args()

    d = _DEFAULTS[args.stage]
    docs = args.docs or d["docs"]
    claims = args.claims or d["claims"]
    mpd = args.max_per_doc or d["max_per_doc"]

    exclude: set[str] = set()
    if args.exclude_manifest:
        exclude = set(json.loads(Path(args.exclude_manifest).read_text())["pmcids"])

    rng = random.Random(args.seed)
    result = sampling.build_stage(docs, claims, mpd, rng, exclude_pmcids=exclude,
                                  log=lambda m: print(m, file=sys.stderr))

    out = Path(args.out)
    export.write_annotation_workbook(result["claims"], out)
    export.write_manifest(result["pmcids"], args.stage, out / "manifest.json")
    export.write_codebook(out / "codebook.json")
    print(f"stage={args.stage}  docs={len(result['pmcids'])}  claims={len(result['claims'])}")
    print(f"-> {out}/  (annotation_A.csv, annotation_B.csv, claims.json, manifest.json, "
          f"codebook.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

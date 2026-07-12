"""Score an annotated external-validation corpus against the FROZEN v2 rule.

Inputs: the two annotators' filled CSVs, the claims.json, and an optional adjudication
CSV (claim_id + resolved fields for disagreements). Outputs inter-annotator kappa/alpha,
adjudicated-gold rule metrics (precision/recall/F1/coverage vs sentence- and document-gold),
recall on true epistemic errors, the context-revision share, and a per-locus breakdown.

Applies v2; does not modify it. Run only after annotation is complete.

    python scripts/evaluate_external_validation.py --dir <corpus_dir> [--adjudication adj.csv]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.external_validation import (  # noqa: E402
    evaluate,
)
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules  # noqa: E402

_FIELDS = ("gold_sentence_class", "gold_document_class", "effect_size_locus", "error_type")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="corpus dir with annotation_A/B.csv + claims.json")
    ap.add_argument("--adjudication", help="CSV resolving disagreements (claim_id + fields)")
    ap.add_argument("--out", help="write report JSON here (default <dir>/eval_report.json)")
    args = ap.parse_args()

    d = Path(args.dir)
    a = evaluate.load_workbook(d / "annotation_A.csv")
    b = evaluate.load_workbook(d / "annotation_B.csv")
    claims = json.loads((d / "claims.json").read_text())
    adj = evaluate.load_workbook(Path(args.adjudication)) if args.adjudication else None

    reliability = {fld: evaluate.agreement(a, b, fld) for fld in _FIELDS}
    built = evaluate.build_gold(a, b, adj, _FIELDS)
    metrics = evaluate.evaluate_rule(claims, built["gold"],
                                     rules.detect_significance_not_importance_v2)

    report = {
        "n_claims": len(claims), "n_gold": len(built["gold"]),
        "n_dropped_unadjudicated": len(built["dropped"]),
        "inter_annotator": reliability, "v2_metrics": metrics,
    }
    out = Path(args.out) if args.out else d / "eval_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

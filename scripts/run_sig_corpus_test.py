"""LLM-free hardening test of R1 on the significance corpus (dev/test split).

Measures precision/recall/F1 of each available significance detector on the dev and
(held-out) test splits, and prints the specific items each one misses / false-fires.
v2 (if present) is developed on the dev split only; the test split is the blind check.

    python scripts/run_sig_corpus_test.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.sig_corpus.items import split  # noqa: E402


def prf(items, det) -> dict:
    tp = fp = fn = 0
    miss, false_pos = [], []
    for it in items:
        pred = det(it.text)
        if it.is_sig and pred:
            tp += 1
        elif it.is_sig and not pred:
            fn += 1
            miss.append(it.id)
        elif (not it.is_sig) and pred:
            fp += 1
            false_pos.append(it.id)
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3),
            "tp": tp, "fp": fp, "fn": fn, "missed": miss, "false_positives": false_pos}


def main() -> int:
    detectors = {"v1": rules.detect_significance_not_importance}
    if hasattr(rules, "detect_significance_not_importance_v2"):
        detectors["v2"] = rules.detect_significance_not_importance_v2

    out = {}
    for name, det in detectors.items():
        out[name] = {sp: prf(split(sp), det) for sp in ("dev", "test")}
        for sp in ("dev", "test"):
            r = out[name][sp]
            print(f"{name} {sp:4s}: P {r['precision']}  R {r['recall']}  F1 {r['f1']}  "
                  f"(tp{r['tp']} fp{r['fp']} fn{r['fn']})")
            if r["missed"]:
                print(f"        missed: {r['missed']}")
            if r["false_positives"]:
                print(f"        FALSE POSITIVES: {r['false_positives']}")
    (Path(__file__).resolve().parents[1]
     / "src/desi/case_studies/marcognity_muse_spark/redteam/sig_corpus/sig_corpus_scorecard.json"
     ).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

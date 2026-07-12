"""Test the DESi thesis on hard2: does a deterministic rule add accuracy over the LLM?

'LLM for language, rules for logic'. Takes a model's stored hard2 reviewer runs,
applies the two deterministic rules in ``redteam/hard2/rules.py`` as a post-layer,
and re-scores. Reports baseline vs +rule (F1/P/R/exact), the two target flags'
recall/false-positives, and every item the rule changed — honestly, including any
new errors. No LLM call, no gold peeking.

    python scripts/run_hard2_rule_test.py --model-slug granite_8b
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.hard import score  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import prompt, rules  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import (  # noqa: E402
    HARD2_ITEMS,
    Flag2,
)

_RUNS = (Path(__file__).resolve().parents[1]
         / "src/desi/case_studies/marcognity_muse_spark/redteam/hard2/external_runs")
_TEXT = {it.id: it.text for it in HARD2_ITEMS}


def _flag_recall(runs, flag):
    tp = fn = 0
    for it in HARD2_ITEMS:
        if flag in it.gold:
            for r in runs:
                tp += flag in r.get(it.id, set())
                fn += flag not in r.get(it.id, set())
    return round(tp / (tp + fn), 3) if tp + fn else None


def _flag_fp(runs, flag):
    return sum(flag in r.get(it.id, set())
              for it in HARD2_ITEMS if flag not in it.gold for r in runs)


def evaluate(slug: str) -> dict:
    base_runs = []
    for f in sorted(glob.glob(str(_RUNS / slug / "run_*.txt"))):
        t = Path(f).read_text()
        if "{" in t:
            base_runs.append(prompt.parse_answer(t))
    if not base_runs:
        raise SystemExit(f"no parseable runs for slug {slug!r}")
    aug_runs = [{iid: rules.apply_rules(_TEXT[iid], fl) for iid, fl in run.items()}
                for run in base_runs]
    b = score.score_runs(slug, base_runs, HARD2_ITEMS)
    a = score.score_runs(f"{slug}+rule", aug_runs, HARD2_ITEMS)
    changed = sorted({it.id for it in HARD2_ITEMS
                      for br, ar in zip(base_runs, aug_runs)
                      if br.get(it.id, set()) != ar.get(it.id, set())})
    return {
        "slug": slug, "runs": len(base_runs),
        "baseline": {k: b[k] for k in ("f1_mean", "f1_stdev", "precision_mean",
                                       "recall_mean", "exact_match_mean")},
        "with_rule": {k: a[k] for k in ("f1_mean", "f1_stdev", "precision_mean",
                                        "recall_mean", "exact_match_mean")},
        "delta_f1": round(a["f1_mean"] - b["f1_mean"], 3),
        "target_flags": {
            fl.value: {
                "recall": [_flag_recall(base_runs, fl), _flag_recall(aug_runs, fl)],
                "false_positives": [_flag_fp(base_runs, fl), _flag_fp(aug_runs, fl)],
            } for fl in (Flag2.SIGNIFICANCE_NOT_IMPORTANCE, Flag2.OVERCLAIM)
        },
        "items_changed": changed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-slug", default="granite_8b")
    args = ap.parse_args()
    r = evaluate(args.model_slug)
    b, a = r["baseline"], r["with_rule"]
    print(f"{r['slug']}  ({r['runs']} runs)")
    print(f"  baseline    F1 {b['f1_mean']:.3f}±{b['f1_stdev']:.3f}  "
          f"P {b['precision_mean']:.3f}  R {b['recall_mean']:.3f}  "
          f"exact {b['exact_match_mean']:.3f}")
    print(f"  + DESi-rule F1 {a['f1_mean']:.3f}±{a['f1_stdev']:.3f}  "
          f"P {a['precision_mean']:.3f}  R {a['recall_mean']:.3f}  "
          f"exact {a['exact_match_mean']:.3f}   (ΔF1 {r['delta_f1']:+.3f})")
    for fl, d in r["target_flags"].items():
        print(f"  {fl:26s} recall {d['recall'][0]}->{d['recall'][1]}  "
              f"FP {d['false_positives'][0]}->{d['false_positives'][1]}")
    print(f"  items changed by rule: {r['items_changed']}")
    print(json.dumps(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

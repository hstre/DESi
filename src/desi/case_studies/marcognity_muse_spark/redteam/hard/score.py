"""Multi-label scoring for the HARD benchmark: precision / recall / F1, exact-match,
per-difficulty and per-item breakdowns, and stability across repeated runs."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from .items import HARD_ITEMS, HardItem


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    prec = tp / (tp + fp) if (tp + fp) else 1.0
    rec = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return round(prec, 3), round(rec, 3), round(f1, 3)


def _score_one_run(run: dict[str, set], items=HARD_ITEMS) -> dict:
    tp = fp = fn = exact = 0
    by_diff: dict[str, list[int]] = {}
    for it in items:
        raised = set(run.get(it.id, set()))
        gold = set(it.gold)
        tp += len(raised & gold)
        fp += len(raised - gold)
        fn += len(gold - raised)
        ex = int(raised == gold)
        exact += ex
        d = by_diff.setdefault(it.difficulty, [0, 0])
        d[0] += ex
        d[1] += 1
    prec, rec, f1 = _prf(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1,
            "exact_match": round(exact / len(items), 3),
            "exact_by_difficulty": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_diff.items())}}


def score_runs(name: str, runs: list[dict[str, set]], items=HARD_ITEMS) -> dict:
    per_run = [_score_one_run(r, items) for r in runs]
    f1s = [r["f1"] for r in per_run]
    exact = [r["exact_match"] for r in per_run]

    # per-item catch fraction across runs (how often the reviewer matched gold exactly)
    item_exact: dict[str, float] = {}
    item_errors: dict[str, list[str]] = {}
    for it in items:
        hits = 0
        errs: list[str] = []
        for r in runs:
            raised = set(r.get(it.id, set()))
            gold = set(it.gold)
            if raised == gold:
                hits += 1
            else:
                miss = ",".join(sorted(f.value for f in (gold - raised)))
                over = ",".join(sorted(f.value for f in (raised - gold)))
                errs.append(("miss:" + miss if miss else "") + ("|over:" + over if over else ""))
        item_exact[it.id] = round(hits / len(runs), 3) if runs else 0.0
        if errs:
            item_errors[it.id] = errs

    return {
        "reviewer": name,
        "runs": len(runs),
        "f1_mean": round(statistics.mean(f1s), 3) if f1s else 0.0,
        "f1_stdev": round(statistics.pstdev(f1s), 3) if len(f1s) > 1 else 0.0,
        "exact_match_mean": round(statistics.mean(exact), 3) if exact else 0.0,
        "precision_mean": round(statistics.mean(r["precision"] for r in per_run), 3),
        "recall_mean": round(statistics.mean(r["recall"] for r in per_run), 3),
        "per_run": per_run,
        "item_exact_rate": item_exact,
        "item_errors": item_errors,
    }


def gold_table(items=HARD_ITEMS) -> list[dict]:
    def row(it: HardItem) -> dict:
        return {"id": it.id, "gold": sorted(f.value for f in it.gold),
                "difficulty": it.difficulty, "debatable": it.debatable,
                "pair": it.pair, "tell": it.tell}
    return [row(it) for it in items]


def write_scorecard(path: Path, scores: list[dict], items=HARD_ITEMS) -> None:
    card = {"gold": gold_table(items), "n_items": len(items), "scores": scores}
    path.write_text(json.dumps(card, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


__all__ = ["score_runs", "gold_table", "write_scorecard"]

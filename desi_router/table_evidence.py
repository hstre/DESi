"""The routing table as a LIVING measurement - re-fit scores from accumulated ledger evidence.

``routing_table.json`` is honest because every score was measured - but it was measured ONCE.
The pipeline already logs every attempt (``pipeline_attempt``: task, model, cost, and - when an
eval-time scorer attached a correctness signal - the realized score) to the shared local
Layer 9 ledger, and ``escalation_evidence`` reads the escalation side of that. This module is
the missing half: read the same events per (task, model) cell and re-fit the table's ``score``
from realized evidence once enough SCORED attempts exist.

Honesty rules:
  * only *scored* attempts count (production attempts without a gold signal never move a score);
  * a cell moves only at ``min_scored`` or more scored attempts (default 30) - no flapping on
    three lucky samples;
  * a refitted cell is *marked*: ``score_source: "ledger-refit"`` plus a ``refit`` block with
    the sample size and the previous benchmark score, and the policy surfaces that source - a
    re-fitted number never masquerades as the original benchmark measurement;
  * a (task, model) pair the table has never measured is appended as an explicitly
    ``provisional`` cell, never silently blended into the benchmark rows;
  * the CLI is dry-run by default; ``--refit`` writes.

Deterministic, stdlib-only, no LLM anywhere.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from desi_router.routing_table import _TABLE_PATH


def measured_evidence(ledger) -> dict:
    """Aggregate realized evidence per (task_class, model): scored-attempt count, mean realized
    score, mean cost. Pure read over ``pipeline_attempt`` events; attempts without a score are
    counted (``n_total``) but never enter the mean."""
    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"n_total": 0, "scores": [], "costs": []})
    for event in ledger.all(kind="pipeline_attempt"):
        p = event["payload"]
        key = (str(p.get("task_class", "unknown")), str(p.get("model", "unknown")))
        a = agg[key]
        a["n_total"] += 1
        if p.get("score") is not None:
            a["scores"].append(float(p["score"]))
        if p.get("cost_usd") is not None:
            a["costs"].append(float(p["cost_usd"]))
    out: dict[str, dict[str, dict]] = {}
    for (task, model), a in sorted(agg.items()):
        out.setdefault(task, {})[model] = {
            "n_total": a["n_total"],
            "n_scored": len(a["scores"]),
            "realized_score": (round(sum(a["scores"]) / len(a["scores"]), 4)
                               if a["scores"] else None),
            "mean_cost_usd": (round(sum(a["costs"]) / len(a["costs"]), 6)
                              if a["costs"] else None),
        }
    return out


def plan_refit(table: dict, evidence: dict, *, min_scored: int = 30) -> list[dict]:
    """Which cells WOULD move, given the evidence - the dry-run view. Returns one entry per
    change: update (an existing cell's score moves) or append (a provisional cell for a pair the
    benchmark never measured). A task class the table does not know is reported, never created -
    task classes are structural, not statistical."""
    changes: list[dict] = []
    tasks = table.get("tasks", {})
    for task, models in sorted(evidence.items()):
        info = tasks.get(task)
        for model, ev in sorted(models.items()):
            if ev["n_scored"] < min_scored or ev["realized_score"] is None:
                continue
            if info is None:
                changes.append({"action": "unknown_task", "task": task, "model": model,
                                "n_scored": ev["n_scored"]})
                continue
            cell = next((c for c in info.get("cells", []) if c.get("model") == model), None)
            if cell is None:
                changes.append({"action": "append", "task": task, "model": model,
                                "score": ev["realized_score"], "n_scored": ev["n_scored"],
                                "mean_cost_usd": ev["mean_cost_usd"]})
            elif round(float(cell.get("score", 0.0)), 4) != ev["realized_score"]:
                changes.append({"action": "update", "task": task, "model": model,
                                "prev_score": cell.get("score"),
                                "score": ev["realized_score"], "n_scored": ev["n_scored"]})
    return changes


def refit(ledger, *, table_path: str | Path | None = None, min_scored: int = 30,
          write: bool = False) -> dict:
    """Re-fit the table from ledger evidence. Dry-run unless ``write=True``. Returns a summary
    with the planned/applied changes; applied cells carry ``score_source: "ledger-refit"`` and a
    ``refit`` provenance block so a re-fitted number never poses as the original benchmark."""
    path = Path(table_path) if table_path else _TABLE_PATH
    table = json.loads(path.read_text(encoding="utf-8"))
    evidence = measured_evidence(ledger)
    changes = plan_refit(table, evidence, min_scored=min_scored)
    if write:
        for ch in changes:
            if ch["action"] == "unknown_task":
                continue
            cells = table["tasks"][ch["task"]].setdefault("cells", [])
            refit_block = {"n_scored": ch["n_scored"],
                           "prev_score": ch.get("prev_score")}
            if ch["action"] == "update":
                cell = next(c for c in cells if c.get("model") == ch["model"])
                cell["score"] = ch["score"]
                cell["score_source"] = "ledger-refit"
                cell["refit"] = refit_block
            else:                                     # append: an unmeasured pair, marked as such
                cells.append({"model": ch["model"], "score": ch["score"],
                              "cost_per_item_usd": ch.get("mean_cost_usd") or 0.0,
                              "score_source": "ledger-refit", "provisional": True,
                              "refit": refit_block})
        path.write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        from desi_router import routing_table
        routing_table._load.cache_clear()             # the cached view must see the new file
    return {"changes": changes, "applied": bool(write and changes),
            "min_scored": min_scored,
            "evidence_tasks": {t: len(m) for t, m in evidence.items()}}


def main() -> None:
    import argparse

    from desi_router.ledger import Ledger
    ap = argparse.ArgumentParser(description="Re-fit routing_table.json from ledger evidence "
                                             "(dry-run by default).")
    ap.add_argument("ledger", help="path to the shared desi_ledger.db")
    ap.add_argument("--table", default=None, help="table path (default: the packaged table)")
    ap.add_argument("--min-scored", type=int, default=30)
    ap.add_argument("--refit", action="store_true", help="actually write the table")
    args = ap.parse_args()
    led = Ledger(args.ledger)
    try:
        out = refit(led, table_path=args.table, min_scored=args.min_scored, write=args.refit)
    finally:
        led.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not args.refit and out["changes"]:
        print("\n(dry-run - nothing written; pass --refit to apply)")


if __name__ == "__main__":
    main()

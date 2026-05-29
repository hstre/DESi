"""Deterministic options × criteria decision record (offline, replay-hashed, no LLM).

Turns an alternative comparison into a transparent, reproducible artifact: weighted ranking +
the explicit tradeoff(s) behind the recommendation. The point is human usefulness — making a
decision auditable and re-runnable — not a score. Re-running on the same spec yields the same
record and the same replay hash.

Spec shape:
    options  : [str, ...]
    criteria : [{"name": str, "weight": float, "higher_is_better": bool}, ...]
    scores   : {option: {criterion: float in [0,1]}}
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from desi.core.replay_kernel import replay_hash  # noqa: E402


def _weighted(option, criteria, scores) -> float:
    total = 0.0
    wsum = sum(c["weight"] for c in criteria) or 1.0
    for c in criteria:
        v = float(scores.get(option, {}).get(c["name"], 0.0))
        if not c.get("higher_is_better", True):
            v = 1.0 - v
        total += c["weight"] * v
    return round(total / wsum, 4)


def _tradeoffs(top, runner, criteria, scores):
    """Criteria where the runner-up beats the winner — the price of choosing the winner."""
    out = []
    for c in criteria:
        name = c["name"]
        wv = float(scores.get(top, {}).get(name, 0.0))
        rv = float(scores.get(runner, {}).get(name, 0.0))
        better_for_runner = (rv > wv) if c.get("higher_is_better", True) else (rv < wv)
        if better_for_runner:
            out.append({"criterion": name, "winner": wv, "runner_up": rv,
                        "note": f"{runner} is stronger on {name} ({rv} vs {wv})"})
    return out


def decide(options, criteria, scores) -> dict:
    ranking = sorted(
        ({"option": o, "score": _weighted(o, criteria, scores)} for o in options),
        key=lambda r: (-r["score"], r["option"]))
    record = {
        "options": list(options),
        "criteria": [{"name": c["name"], "weight": c["weight"],
                      "higher_is_better": bool(c.get("higher_is_better", True))} for c in criteria],
        "ranking": ranking,
        "winner": ranking[0]["option"] if ranking else None,
        "decisive_margin": round(ranking[0]["score"] - ranking[1]["score"], 4) if len(ranking) > 1 else None,
        "tradeoffs": _tradeoffs(ranking[0]["option"], ranking[1]["option"], criteria, scores)
        if len(ranking) > 1 else [],
    }
    record["replay_hash"] = replay_hash({k: v for k, v in record.items()})
    return record


def format_record(record: dict) -> str:
    md = ["# Decision record\n",
          f"**Recommended:** {record['winner']}  (margin {record['decisive_margin']})\n",
          "## Ranking", "| rank | option | score |", "| --- | --- | --- |"]
    for n, r in enumerate(record["ranking"], 1):
        md.append(f"| {n} | {r['option']} | {r['score']} |")
    md += ["", "## Explicit tradeoffs (price of the recommendation)"]
    if record["tradeoffs"]:
        for t in record["tradeoffs"]:
            md.append(f"- {t['note']}")
    else:
        md.append("- none — the recommended option is not dominated on any criterion.")
    md += ["", f"replay_hash: {record['replay_hash'][:16]}"]
    return "\n".join(md) + "\n"

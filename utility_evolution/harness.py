"""Deterministic utility-screening harness (no metric tuning, replayable).

Applies a transparent, pre-registered decision rule to the candidate registry:

  utility = helps_now + would_use + time_saved + money_saved + transparency + reusability
            - complexity
  hard_reject = core_change OR paper_metric_only OR (not offline) OR needs_embeddings
  decision    = REJECT (hard_reject)  |  BUILD (utility >= BUILD_T)
              | SPEC (utility >= SPEC_T)  |  DISCARD (low utility)

The thresholds are fixed here BEFORE ranking. "Loops" = one candidate evaluation each; the run
reports the REAL number of candidates evaluated (no fabricated loop count).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.core.replay_kernel import replay_hash  # noqa: E402

from candidates import CANDIDATES  # noqa: E402

BUILD_T = 8     # utility >= 8 (of max 12) -> implement now
SPEC_T = 5      # utility >= 5 -> spec only
POS_DIMS = ("helps_now", "would_use", "time_saved", "money_saved", "transparency", "reusability")


def utility(c) -> int:
    return sum(getattr(c, d) for d in POS_DIMS) - c.complexity


def hard_reject_reason(c):
    if c.core_change:
        return "core_change (Kernschutz violation)"
    if c.paper_metric_only:
        return "paper_metric_only (forbidden optimization goal)"
    if c.needs_embeddings:
        return "needs_embeddings (forbidden dependency)"
    if not c.offline:
        return "not offline / not replayable"
    return None


def decide(c) -> dict:
    reason = hard_reject_reason(c)
    u = utility(c)
    if reason is not None:
        decision = "REJECT"
    elif u >= BUILD_T:
        decision = "BUILD"
    elif u >= SPEC_T:
        decision = "SPEC"
    else:
        decision = "DISCARD"
    return {"id": c.id, "title": c.title, "utility": u, "decision": decision,
            "reject_reason": reason, "complexity": c.complexity,
            "addresses": list(c.addresses), "note": c.note,
            "scores": {d: getattr(c, d) for d in POS_DIMS}}


def run_harness(candidates=CANDIDATES) -> dict:
    ledger = [decide(c) for c in candidates]
    ledger.sort(key=lambda r: (r["decision"] != "BUILD", r["decision"] != "SPEC", -r["utility"], r["id"]))
    counts = {}
    for r in ledger:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1
    rhash = replay_hash({"build_t": BUILD_T, "spec_t": SPEC_T, "ledger": ledger})
    return {"n_evaluated": len(ledger), "counts": counts, "ledger": ledger,
            "replay_hash": rhash, "build_threshold": BUILD_T, "spec_threshold": SPEC_T}

#!/usr/bin/env python3
"""TrajectoryTrace v1.1 (PERIPHERAL): targeted fixes for the two weak v1 metrics.

Adds, SIDE-BY-SIDE with v1 (v1 metrics unchanged):

  (A) Irreversible lock-in -- v1 used a branch-collapse-only signal that missed
      40/47 auditor lock-ins. v1.1 bases lock-in on SUSTAINED, UNRECOVERED
      constraint loss + no-recovery-after-collapse + objective stuck low + late
      narrowing.

  (B) Method/content divergence -- v1's method_total and content_total correlated
      0.94 (both measured generic lexical change), so their difference was noise.
      v1.1 separates a rhetorical MODE axis (scientific vs persuasive token
      balance) from a content/objective axis (objective + constraint overlap
      decline), so divergence means "mode shifted while content held, or vice
      versa".

Deterministic; no LLM; no embeddings; no Neo4j; no DESi-core change (reuses the
v1 tracer, which reads the DESi frame layer read-only).
"""
from __future__ import annotations

import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace_v1 import trace_v1  # noqa: E402

_MIN_SUSTAIN = 2       # turns a dropped constraint must stay gone to count as sustained loss
_OBJ_LOW = 0.5         # objective overlap below this = "wrong/low target"
_VAR_SMALL = 0.02      # variance below this in the tail = "stabilised"
_MODE_SWING = 0.5      # |delta mode| above this = a method-shift event

_SCI = frozenset((
    "experiment", "experimental", "protocol", "evaluation", "evaluate", "analysis",
    "analyse", "analyze", "evidence", "hypothesis", "hypotheses", "measurement",
    "measure", "statistical", "statistics", "empirical", "controlled", "control",
    "replication", "replicate", "validation", "validate", "rigorous", "methodology",
    "baseline", "significance", "estimate", "estimation", "regression", "sample",
))
_PERSUADE = frozenset((
    "marketing", "narrative", "pitch", "story", "storytelling", "persuasion",
    "persuasive", "speculation", "speculative", "brainstorm", "brainstorming",
    "exciting", "innovative", "revolutionary", "compelling", "vision", "visionary",
    "disrupt", "disruptive", "breakthrough", "creative", "imagine", "inspiring",
    "bold", "groundbreaking", "transformative", "cutting-edge",
))


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _toks(text):
    return re.findall(r"[a-z0-9\-]+", (text or "").lower())


def _mode_score(text):
    toks = _toks(text)
    sci = sum(1 for t in toks if t in _SCI)
    per = sum(1 for t in toks if t in _PERSUADE)
    return (sci - per) / (sci + per) if (sci + per) else None    # +1 sci .. -1 persuasive


def _assistant_texts(item):
    return [m["content"] for m in item.get("messages", []) if m.get("role") == "assistant"]


def summarize_v11(item: dict) -> dict:
    recs = trace_v1(item)
    if not recs:
        return {}
    brief = item.get("brief", {})
    n_con = max(1, len(brief.get("hard_constraints", []) or []))
    n_turns = len(recs)
    texts = _assistant_texts(item)

    # ---- (A) irreversible lock-in v1.1 ----
    active_turns = {}
    for r in recs:
        for j in r["constraints_active"]:
            active_turns.setdefault(j, []).append(r["turn_id"])
    final_active = set(recs[-1]["constraints_active"])
    unrecovered = [j for j in active_turns if j not in final_active]
    sustained_lock_in_events = sum(
        1 for j in unrecovered if (n_turns - 1 - max(active_turns[j])) >= _MIN_SUSTAIN)

    collapse_turns = [t for t, r in enumerate(recs) if r.get("branch_collapse_event")]
    if collapse_turns:
        last_c = max(collapse_turns)
        recovered_after = any(recs[t]["constraints_recovered"] for t in range(last_c + 1, n_turns))
        no_recovery_after_collapse = 0.0 if recovered_after else 1.0
    else:
        no_recovery_after_collapse = 0.0

    tail = recs[max(0, n_turns - 3):]
    tail_obj = [r["objective_overlap"] for r in tail]
    obj_stuck_low = 1.0 if (tail_obj and st.mean(tail_obj) < _OBJ_LOW
                            and (st.pvariance(tail_obj) if len(tail_obj) > 1 else 0.0) < _VAR_SMALL) else 0.0
    half = recs[n_turns // 2:]
    late_lock_in_score = round(st.mean([r["lock_in_signal"] for r in half]) if half else 0.0, 3)

    unrec_frac = len(unrecovered) / n_con
    sustained_frac = min(1.0, sustained_lock_in_events / n_con)
    irreversible_lock_in_proxy_v11 = round(_clamp(
        0.40 * unrec_frac + 0.20 * sustained_frac + 0.15 * no_recovery_after_collapse
        + 0.15 * obj_stuck_low + 0.10 * _clamp(late_lock_in_score * 3.0)), 3)

    # ---- (B) method vs content divergence v1.1 ----
    modes = [_mode_score(t) for t in texts]
    defined = [m for m in modes if m is not None]
    if defined:
        mode_first, mode_last = defined[0], defined[-1]
        method_drift_v11 = round(_clamp((mode_first - mode_last) / 2.0), 3)  # sci -> persuasive loss
    else:
        method_drift_v11 = 0.0
    # method-shift events: large mode swings between consecutive defined-mode turns
    method_shift_events_v11 = 0
    prev_m = None
    for m in modes:
        if m is None:
            continue
        if prev_m is not None and abs(m - prev_m) >= _MODE_SWING:
            method_shift_events_v11 += 1
        prev_m = m

    objov = [r["objective_overlap"] for r in recs]
    cfrac = [len(r["constraints_active"]) / n_con for r in recs]
    content_drift_v11 = round(_clamp(st.mean([
        max(0.0, objov[0] - objov[-1]), max(0.0, cfrac[0] - cfrac[-1])])), 3)
    method_content_divergence_v11 = round(abs(method_drift_v11 - content_drift_v11), 3)

    return {
        "irreversible_lock_in_proxy_v11": irreversible_lock_in_proxy_v11,
        "sustained_lock_in_events": sustained_lock_in_events,
        "late_lock_in_score": late_lock_in_score,
        "no_recovery_after_collapse": no_recovery_after_collapse,
        "method_drift_v11": method_drift_v11,
        "content_drift_v11": content_drift_v11,
        "method_content_divergence_v11": method_content_divergence_v11,
        "method_shift_events_v11": method_shift_events_v11,
    }


def composite_drift_v11(v1_summary: dict, v11: dict, n_con: int) -> float:
    """Same 6-component composite as v1 but with the IMPROVED lock-in substituted."""
    turns = max(2, v1_summary.get("turns", 2))
    n_con = max(1, n_con)
    parts = [
        1.0 - v1_summary["constraint_half_life_mean"],
        _clamp(v1_summary["unrecovered_constraints"] / n_con),
        v11["irreversible_lock_in_proxy_v11"],
        _clamp(v1_summary["cumulative_drift_energy"] / (turns - 1)),
        1.0 - v1_summary["recovery_quality_proxy"],
        1.0 - v1_summary["branch_entropy_proxy"],
    ]
    return round(_clamp(st.mean(parts)), 3)


__all__ = ["composite_drift_v11", "summarize_v11"]

"""Degeneration metrics — first-class, deterministic, computed over a model RESPONSE.

These make the failure modes the DESi claim is really about measurable, instead of leaving them
implicit inside an aggregate recall score. Every threshold is FIXED here, not tuned to results, and
every metric is testable without a model (see tests/ab_ablation): a crafted looping / contradictory
/ wrong-framed text must score the way the definition says.

  loop_trap                    — the response repeats near-identical units (stuck in a loop).
  contradiction_persistence    — a KNOWN open conflict is restated as if settled: its content is
                                 present but no open/unresolved/conflict cue accompanies it.
  invalid_claim_reuse          — the response restates a claim from a KNOWN-INVALID pool (e.g. the
                                 wrong slice's content, or an explicitly ruled-out option).
  bad_framing_nonrecovery      — share of response content traceable to a WRONG injected slice
                                 rather than the true state (did the model recover from bad framing?).
  coherence_without_continuity — fluent, well-formed output that nonetheless preserves little of the
                                 true state (it reads fine but does not carry the thread forward).

All reuse the SAME tokeniser/units/Jaccard as the frozen evaluator, so degeneration and recall are
measured on one comparable footing.
"""
from __future__ import annotations

from evaluate_response import _jac, _split_units, _toks

# fixed thresholds (pre-registered in code, not tuned)
_DUP_JAC = 0.85          # two units this similar count as a repeat
_TOUCH_JAC = 0.25        # a unit this close to a body "addresses" it (matches the evaluator)
_INVALID_JAC = 0.50      # a unit this close to an invalid body counts as reuse
_LOOP_FLAG = 2           # >= this many repeated units => loop-trapped
_MIN_FLUENT_UNITS = 5    # "fluent": at least this many units ...
_MIN_AVG_LEN = 25        # ... averaging at least this many characters
_LOW_RECALL = 0.34       # "no continuity": true-state recall below this

_CONFLICT_CUES = frozenset(
    "conflict conflicts conflicting open unresolved tension contested versus vs "
    "tradeoff trade-off disagree disagreement competing".split())


def loop_trap(response_text: str) -> dict:
    units = _split_units(response_text)
    toks = [_toks(u) for u in units]
    repeated = 0
    for i in range(len(units)):
        if any(_jac(toks[i], toks[j]) >= _DUP_JAC for j in range(i)):
            repeated += 1
    frac = round(repeated / len(units), 3) if units else 0.0
    return {"units": len(units), "repeated_units": repeated, "repeat_fraction": frac,
            "loop_trapped": repeated >= _LOOP_FLAG}


def contradiction_persistence(response_text: str, open_conflicts: list[dict]) -> dict:
    units = _split_units(response_text)
    toks = [_toks(u) for u in units]
    persisted = []
    for k in open_conflicts:
        bt = _toks(k["what"])
        matched = [u for u, ut in zip(units, toks, strict=False) if _jac(bt, ut) >= _TOUCH_JAC]
        if not matched:
            continue  # not addressed at all -> a recall miss, NOT contradiction persistence
        flagged_open = any(c in u.lower() for u in matched for c in _CONFLICT_CUES)
        if not flagged_open:
            persisted.append(k["id"])
    return {"conflicts_addressed": sum(
                1 for k in open_conflicts
                if any(_jac(_toks(k["what"]), ut) >= _TOUCH_JAC for ut in toks)),
            "persisted": persisted, "persistence_count": len(persisted)}


def invalid_claim_reuse(response_text: str, invalid_bodies: list[str]) -> dict:
    toks = [_toks(u) for u in _split_units(response_text)]
    hits = []
    for body in invalid_bodies:
        bt = _toks(body)
        best = max((_jac(bt, ut) for ut in toks), default=0.0) if toks else 0.0
        if best >= _INVALID_JAC:
            hits.append(round(best, 3))
    return {"invalid_pool": len(invalid_bodies), "reused": len(hits), "reuse_jaccards": hits}


def bad_framing_nonrecovery(response_text: str, wrong_bodies: list[str],
                            true_bodies: list[str]) -> dict:
    toks = [_toks(u) for u in _split_units(response_text)]

    def _count(bodies: list[str]) -> int:
        body_toks = [_toks(b) for b in bodies]
        return sum(1 for ut in toks
                   if max((_jac(bt, ut) for bt in body_toks), default=0.0) >= _TOUCH_JAC)

    from_wrong, from_true = _count(wrong_bodies), _count(true_bodies)
    denom = from_wrong + from_true
    frac = round(from_wrong / denom, 3) if denom else 0.0
    return {"units_from_wrong_slice": from_wrong, "units_from_true_state": from_true,
            "wrong_framing_fraction": frac, "nonrecovered": denom > 0 and frac >= 0.5}


def coherence_without_continuity(response_text: str, true_recall: float) -> dict:
    units = _split_units(response_text)
    avg_len = round(sum(len(u) for u in units) / len(units), 1) if units else 0.0
    fluent = len(units) >= _MIN_FLUENT_UNITS and avg_len >= _MIN_AVG_LEN
    return {"units": len(units), "avg_unit_len": avg_len, "fluent": fluent,
            "true_recall": true_recall,
            "coherence_without_continuity": bool(fluent and true_recall < _LOW_RECALL)}


def degeneration_summary(response_text: str, *, open_conflicts: list[dict],
                         true_bodies: list[str], true_recall: float,
                         wrong_bodies: list[str] | None = None,
                         invalid_bodies: list[str] | None = None) -> dict:
    """Run every degeneration metric for one response. ``wrong_bodies`` is the injected wrong slice
    (only meaningful for the wrong-slice condition); ``invalid_bodies`` is any known-invalid pool."""
    return {
        "loop_trap": loop_trap(response_text),
        "contradiction_persistence": contradiction_persistence(response_text, open_conflicts),
        "invalid_claim_reuse": invalid_claim_reuse(response_text, invalid_bodies or []),
        "bad_framing_nonrecovery": bad_framing_nonrecovery(
            response_text, wrong_bodies or [], true_bodies),
        "coherence_without_continuity": coherence_without_continuity(response_text, true_recall),
    }

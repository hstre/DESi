"""Phase 2 — replay the router against the REAL ablation artefacts (deterministic, no LLM).

The question: would the router route *protectively* exactly where the ablation measured degeneration,
and stay *light* where it did not? We do not re-run any model — we read the committed result JSONs,
label each (model, condition) as DEGENERATE or CLEAN from its measured metrics, map the condition to
the epistemic SITUATION the router would see, run ``select_mode`` on it, and check concordance:

    protected  ⟺  degenerate

The honest twist: a *plausible-wrong* or *irrelevant* slice (C / G) only degenerates if the model
trusts it — and the router can only protect against it if DESi/Layer-9 surfaces a **detectable
signal** (low extraction confidence, low state-recall, or a wrong-frame flag). So we run TWO passes:

  * ``signaled``   — Layer-9 flags the bad slice (low confidence / recall / wrong-frame) → router can act.
  * ``unsignaled`` — the bad slice looks clean → router has nothing to act on.

Structural risks (no usable state → retrieval; an open conflict; an empty state) are caught in BOTH
passes because the situation itself is visible. The gap between the two passes is the load-bearing,
non-circular finding: **the router's protection against plausible-wrong state is exactly as good as
DESi's risk signal, no better.**
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from desi_router.governance import modes as M
from desi_router.governance.benchmark.cases import _Snap
from desi_router.governance.modes import select_mode
from desi_router.governance.report import report_from_snapshot

_HERE = Path(__file__).resolve().parents[3] / "ab_evidence" / "results"
_FILES = ["ablation2_phase3_sonnet.json", "ablation2_phase3_gpt4o.json",
          "ablation2_phase5_sonnet.json", "ablation2_phase5_granite.json"]

_PROTECTIVE = {M.GUARDED, M.RECOVERY, M.RETRIEVAL, M.ANTI_DELPHI, M.ASK_USER}

# condition -> family the router situation is built from
_CLEAN = {"B_normal_desi", "E_budget_matched_status_stripped", "B_auto_constructed"}
_NOSTATE = {"F_empty_state", "R1_bm25", "R2_tfidf", "R3_hybrid", "R2n_neural"}
_CONFLICT = {"H_contradiction_wrong"}
_WRONG_SLICE = {"C_wrong_slice", "G_neutral_irrelevant"}
_SKIP = {"A_baseline_full_context", "D_status_stripped"}   # no-governance baseline / near-clean variant


def _degenerate(metrics: dict, recall) -> bool:
    """A (model, condition) point counts as degenerate if recall collapsed OR any degeneration metric
    crossed a clear threshold (rates >= 0.5; the unbounded invalid-claim-reuse count > 0.5)."""
    if recall is not None and recall < 0.6:
        return True
    g = metrics or {}
    return (g.get("invalid_claim_reuse_mean", 0) > 0.5
            or g.get("confidence_while_wrong_rate", 0) >= 0.5
            or g.get("coherence_without_continuity_rate", 0) >= 0.5
            or g.get("contradiction_persistence_mean", 0) >= 0.5
            or g.get("bad_framing_nonrecovery_rate", 0) >= 0.5
            or g.get("loop_trap_rate", 0) >= 0.5)


def _situation(cond: str, *, signaled: bool):
    """Return (report, retrieval_available) for the router situation a condition represents, or None
    if the condition is not mapped. ``signaled`` only matters for the plausible-wrong slices."""
    snap = _Snap()

    def mk(**kw):
        return report_from_snapshot(cond, snap, **kw)

    if cond in _CLEAN:
        return mk(selected_claim_ids=("c1",), selected_claim_texts=("clean working state",),
                  extraction_confidence=0.95, state_recall_estimate=1.0), True
    if cond in _NOSTATE:
        return mk(selected_claim_ids=()), True
    if cond in _CONFLICT:
        snap = _Snap(conflicts=(("k1", "contradiction", ("a", "b")),))
        return report_from_snapshot(cond, snap, selected_claim_ids=("c1",),
                                    selected_claim_texts=("state with a live contradiction",),
                                    answer_requires_conflict_resolution=True,
                                    extraction_confidence=0.9, state_recall_estimate=1.0), True
    if cond in _WRONG_SLICE:
        if signaled:                       # Layer-9 / extraction flags the bad slice
            return mk(selected_claim_ids=("c1",),
                      selected_claim_texts=("a plausible but wrong/irrelevant slice",),
                      extraction_confidence=0.3, state_recall_estimate=0.3,
                      wrong_frame_present=(cond == "C_wrong_slice")), True
        # unsignaled: the wrong slice looks perfectly clean — the router has nothing to act on
        return mk(selected_claim_ids=("c1",),
                  selected_claim_texts=("a plausible but wrong/irrelevant slice",),
                  extraction_confidence=0.95, state_recall_estimate=1.0), True
    return None


def _protected(decision) -> bool:
    return bool(decision.validator_required or decision.chosen_mode in _PROTECTIVE)


def _aggregate(path: Path):
    d = json.loads(path.read_text())
    rec, deg = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for case in d["cases"]:
        for c, cv in case["conditions"].items():
            if cv.get("recall") is not None:
                rec[c].append(cv["recall"])
            for k, v in (cv.get("degeneration") or {}).items():
                if v is not None:
                    deg[c][k].append(v)
    def mean(xs):
        return sum(xs) / len(xs) if xs else None

    return (d.get("model", path.stem),
            {c: mean(v) for c, v in rec.items()},
            {c: {k: mean(vs) for k, vs in deg[c].items()} for c in deg})


def replay(files: list[str] | None = None) -> dict:
    files = files or _FILES
    passes = {"signaled": defaultdict(list), "unsignaled": defaultdict(list)}
    discord = {"signaled": [], "unsignaled": []}
    per_model = {}
    points = 0
    for fn in files:
        p = _HERE / fn
        if not p.exists():
            continue
        model, rec, deg = _aggregate(p)
        per_model.setdefault(model, {"conds": 0})
        for cond in rec:
            if cond in _SKIP or _situation(cond, signaled=True) is None:
                continue
            degen = _degenerate(deg.get(cond, {}), rec.get(cond))
            per_model[model]["conds"] += 1
            points += 1
            for ps in ("signaled", "unsignaled"):
                report, retr = _situation(cond, signaled=(ps == "signaled"))
                dec = select_mode(report, retrieval_available=retr)
                ok = _protected(dec) == degen
                passes[ps]["all"].append(ok)
                passes[ps][_family(cond)].append(ok)
                if not ok:
                    discord[ps].append({"model": model, "condition": cond,
                                        "degenerate": degen, "mode": dec.chosen_mode,
                                        "protected": _protected(dec)})
    conc = {ps: (round(sum(v["all"]) / len(v["all"]), 3) if v["all"] else None)
            for ps, v in passes.items()}
    by_family = {ps: {fam: round(sum(x) / len(x), 3)
                      for fam, x in v.items() if fam != "all"}
                 for ps, v in passes.items()}
    return {"points": points, "models": list(per_model), "concordance": conc,
            "by_family": by_family, "discordant": discord}


def _family(cond: str) -> str:
    if cond in _CLEAN:
        return "clean"
    if cond in _NOSTATE:
        return "no_state/retrieval"
    if cond in _CONFLICT:
        return "open_conflict"
    if cond in _WRONG_SLICE:
        return "plausible_wrong_slice"
    return "other"


def main() -> None:
    r = replay()
    if not r["points"]:
        print("no ablation result files found under ab_evidence/results/ — nothing to replay.")
        return
    print(f"Phase-2 replay · {r['points']} (model,condition) points · "
          f"models: {', '.join(m.split('/')[-1] for m in r['models'])}\n")
    print("Concordance (router protects ⟺ ablation measured degeneration):")
    for ps in ("signaled", "unsignaled"):
        print(f"  {ps:<11}: {r['concordance'][ps]:.2f}")
        for fam, v in sorted(r["by_family"][ps].items()):
            print(f"       {fam:<24} {v:.2f}")
    print("\nDiscordant points (the honest misses):")
    if not r["discordant"]["unsignaled"]:
        print("  none")
    seen = set()
    for d in r["discordant"]["unsignaled"]:
        key = (d["condition"],)
        if key in seen:
            continue
        seen.add(key)
        print(f"  unsignaled · {d['condition']:<22} degenerate={d['degenerate']} "
              f"-> router chose {d['mode']} (protected={d['protected']})")
    print("\nReading: structural risks (no state/retrieval, open conflict) are caught in BOTH passes. "
          "A plausible-wrong slice is caught ONLY when DESi/Layer-9 signals it (low confidence/recall/"
          "wrong-frame). The router's protection against undetectable wrong state is exactly its input "
          "signal — no better. That dependency, not a headline accuracy, is the Phase-2 result.")


if __name__ == "__main__":
    main()

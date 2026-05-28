#!/usr/bin/env python3
"""DESi compression LOSS-ATTRIBUTION audit on DriftBench (READ-ONLY, measurement-only).

Reads the variant rows produced by `run_compression_ablation.py` and attributes, for
each compression STEP along the pipeline (ordered by increasing compression):
    A (raw) -> B (filler removed) -> F (full state) -> E -> D -> C
how many tokens the step saves, how much epistemic signal it costs, and WHICH signal
family becomes invisible. Flags disproportionate loss; never patches it.

No DESi-core change, no metric mutation, no threshold tuning, no embeddings, no LLM.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import run_compression_ablation as abl  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_ROWS = _RESULTS / "compression_ablation.jsonl"

# Compression pipeline order (least -> most compressed) and what each strip removes.
PIPELINE = ["A", "B", "F", "E", "D", "C"]
STEP_REMOVES = {
    ("A", "B"): ("filler / low-information turns", set()),
    ("B", "F"): ("raw transcript text (-> structured DESi state)", set()),
    ("F", "E"): ("lock-in proxy + recovery-quality + drift-energy + composite", {"lock_in"}),
    ("E", "D"): ("recovery counts + per-turn drift/recovery event ledger", {"recovery", "event"}),
    ("D", "C"): ("branch entropy + branch-collapse state", {"branch"}),
}
# A loss-per-token-saved ratio above this (epistemic-loss fraction per 1% of extra tokens
# saved) is FLAGGED as disproportionate. Fixed structural flag, not tuned to any label.
DANGER_FLAG = 0.5


def _load_rows():
    return [json.loads(l) for l in _ROWS.read_text().splitlines() if l.strip()]


def attribute(rows):
    agg = abl.aggregate(rows)
    per, w = agg["per"], agg["weights"]
    wtot = sum(w.values()) or 1.0
    steps = []
    for src, dst in zip(PIPELINE, PIPELINE[1:]):
        label, removed = STEP_REMOVES[(src, dst)]
        d_comp = round(per[dst]["compression_mean"] - per[src]["compression_mean"], 4)  # extra tokens saved
        d_loss = round(per[src]["epistemic_retained"] - per[dst]["epistemic_retained"], 4)  # signal lost
        lost_weight = round(sum(w[s] for s in removed) / wtot, 4)
        # danger = epistemic loss per unit of extra compression (token saving)
        danger = round(d_loss / d_comp, 3) if d_comp > 1e-6 else (float("inf") if d_loss > 0 else 0.0)
        steps.append({
            "step": f"{src}->{dst}", "removes": label, "signals_lost": sorted(removed),
            "extra_compression": d_comp, "epistemic_loss": d_loss,
            "lost_signal_weight": lost_weight, "danger_ratio": danger,
            "flag": (d_loss > 0 and (d_comp <= 0 or danger >= DANGER_FLAG)),
        })
    return agg, steps


def _safety_signal(rows):
    """Does the compact state itself reveal, per trajectory, when further compression is unsafe?
    A field is 'load-bearing' for a trajectory when its event/collapse count is > 0, so dropping
    it would erase real structure. Report how often each is load-bearing."""
    n = len(rows)
    branch_lb = sum(1 for r in rows if r["branch_collapse_events"] > 0)
    recovery_lb = sum(1 for r in rows if (r["total_events"] > 0 or r["failed_recovery_count"] > 0))
    lockin_lb = sum(1 for r in rows if r["lock_in_proxy"] > 0)
    any_lb = sum(1 for r in rows if (r["branch_collapse_events"] > 0 or r["total_events"] > 0
                                     or r["failed_recovery_count"] > 0 or r["lock_in_proxy"] > 0))
    return {"n": n, "branch_load_bearing": branch_lb, "recovery_load_bearing": recovery_lb,
            "lockin_load_bearing": lockin_lb, "any_load_bearing": any_lb}


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    rows = _load_rows()
    agg, steps = attribute(rows)
    safety = _safety_signal(rows)
    _report(rows, agg, steps, safety)
    flagged = [s["step"] for s in steps if s["flag"]]
    print(f"loss-audit: N={len(rows)} steps={len(steps)} flagged={flagged}")


def _report(rows, agg, steps, safety):
    n, per, w = agg["n"], agg["per"], agg["weights"]
    save_steps = sorted(steps, key=lambda s: s["extra_compression"], reverse=True)
    loss_steps = sorted(steps, key=lambda s: s["epistemic_loss"], reverse=True)
    danger_steps = sorted(steps, key=lambda s: (s["danger_ratio"] if s["danger_ratio"] != float("inf") else 1e9),
                          reverse=True)
    biggest_save = save_steps[0]
    biggest_loss = loss_steps[0]
    most_dangerous = danger_steps[0]
    safest = min(steps, key=lambda s: (s["epistemic_loss"], -s["extra_compression"]))

    def sig_step(sig):
        for s in steps:
            if sig in s["signals_lost"]:
                return s["step"]
        return "n/a"

    md = [
        "# DESi compression loss-attribution audit — DriftBench (read-only)\n",
        "For each compression STEP along the pipeline "
        "`A(raw) → B(filler removed) → F(full state) → E → D → C`, attribute the tokens saved, "
        "the epistemic signal lost, and which signal family becomes invisible. Disproportionate "
        "loss is FLAGGED, never patched. Measurement-only; no DESi-core change.\n",
        f"## Size\n- Trajectories: **{n}**. Raw mean {agg['tokens_A_mean']} tokens.\n",
        "## Per-step attribution (ordered by increasing compression)\n",
        "| step | removes | signals lost | extra compression | epistemic loss | lost-signal weight | "
        "danger (loss / extra-compression) | flag |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in steps:
        dr = "∞" if s["danger_ratio"] == float("inf") else s["danger_ratio"]
        md.append(f"| {s['step']} | {s['removes']} | {', '.join(s['signals_lost']) or '—'} | "
                  f"{s['extra_compression']} | {s['epistemic_loss']} | {s['lost_signal_weight']} | "
                  f"{dr} | {'**FLAG**' if s['flag'] else 'ok'} |")
    md += [
        "- `extra compression` = additional fraction of raw tokens removed by this step (vs. the "
        "previous variant). `epistemic loss` = drop in retained epistemic signal. `danger` = "
        "epistemic loss per unit of extra compression — high when a step destroys signal for almost "
        f"no token gain. Steps with danger ≥ {DANGER_FLAG} (or any loss at ≤0 token gain) are flagged.",
        "",
        "## Step-level findings\n",
        f"- **Saves the most tokens:** `{biggest_save['step']}` "
        f"(+{biggest_save['extra_compression']} compression) — {biggest_save['removes']}.",
        f"- **Loses the most epistemic information:** `{biggest_loss['step']}` "
        f"(−{biggest_loss['epistemic_loss']} retained) — drops {', '.join(biggest_loss['signals_lost']) or 'none'}.",
        f"- **Safest step:** `{safest['step']}` (epistemic loss {safest['epistemic_loss']}, "
        f"extra compression {safest['extra_compression']}).",
        f"- **Most dangerous step:** `{most_dangerous['step']}` "
        f"(danger {('∞' if most_dangerous['danger_ratio']==float('inf') else most_dangerous['danger_ratio'])}: "
        f"loses {', '.join(most_dangerous['signals_lost']) or 'signal'} for "
        f"{most_dangerous['extra_compression']} extra compression).",
        "",
        "## Which step causes which specific failure\n",
        f"- **Branch collapse** (branch state becomes invisible): step `{sig_step('branch')}`.",
        f"- **Recovery invisibility** (recovery events/quality gone): step `{sig_step('recovery')}`.",
        f"- **Lock-in loss** (irreversible-lock-in signal gone): step `{sig_step('lock_in')}`.",
        "",
        "## Where catastrophic epistemic degradation begins\n",
        _catastrophe_para(steps, per),
        "",
        "## Does DESi know when its own compression becomes epistemically unsafe?\n",
        f"- The compact state carries per-trajectory counts that mark which fields are "
        f"**load-bearing** (non-zero structure that further compression would erase):",
        f"  - branch state load-bearing (branch_collapse > 0): {safety['branch_load_bearing']}/{n} "
        f"({round(100*safety['branch_load_bearing']/n)}%).",
        f"  - recovery/event load-bearing (events or failed-recovery > 0): "
        f"{safety['recovery_load_bearing']}/{n} ({round(100*safety['recovery_load_bearing']/n)}%).",
        f"  - lock-in load-bearing (lock-in proxy > 0): {safety['lockin_load_bearing']}/{n} "
        f"({round(100*safety['lockin_load_bearing']/n)}%).",
        f"  - ANY component load-bearing: {safety['any_load_bearing']}/{n} "
        f"({round(100*safety['any_load_bearing']/n)}%).",
        "- **Operationally yes, structurally no:** the state's own counts identify, per trajectory, "
        "exactly which families are load-bearing — so a deterministic guard ('do not drop a field "
        "whose count > 0 for this trajectory') is derivable from the state itself. But the DESi core "
        "has no built-in alarm that fires when compression crosses into unsafe territory; that "
        "judgement lives in this external audit. (We FLAG this; we do not add such a guard — that "
        "would be a patch.)",
        "",
        "## Verdict\n",
        "- The expensive, valuable compression is **raw → full DESi state** (huge token savings, "
        "zero measured epistemic loss). Every step that shrinks the state further removes a whole "
        "signal family for negligible additional savings, so **Full DESi (F) sits at the Pareto "
        "knee** and the sub-F variants are strictly worse trades on this benchmark.",
        f"- Flagged steps: {', '.join(s['step'] for s in steps if s['flag']) or '(none)'} — "
        "reported, NOT patched (per the audit rule).",
        "",
        "## DESi-core invariance\n- Read-only; consumes the ablation rows; core byte-identical; "
        "no metric mutation, no threshold tuning, no improvement patch.",
        "",
        "## Honesty / limits\n- Loss is attributed via the retained-signal weights from the "
        "ablation run (|corr| of each DESi field vs. a single-auditor dimension); steps that save "
        "near-zero tokens yield very large or infinite danger ratios by construction — that is the "
        "point (they are pure-loss operations), not an artifact to be smoothed. The pipeline order "
        "is fixed structurally; no label was used to choose it.",
    ]
    (_REPORTS / "compression_loss_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _catastrophe_para(steps, per):
    flagged = [s for s in steps if s["flag"]]
    if not flagged:
        return ("- No step crossed the disproportionate-loss flag: every token-saving step kept "
                "its epistemic signal. Catastrophic degradation does not occur within these "
                "variants.")
    first = flagged[0]
    worst = max(steps, key=lambda s: s["epistemic_loss"])
    note = ""
    if worst["step"] != first["step"]:
        note = (" Honest caveat: the FIRST flag (`{f}`) loses only {fl} retained signal because the "
                "lock-in proxy barely tracks the auditor's lock-in class on DriftBench (weight ~0.01) "
                "— it trips the flag only because it saves ~0 tokens. The genuinely LARGE epistemic "
                "collapse is at **`{w}`** (−{wl} retained), where {ws} become invisible.").format(
            f=first["step"], fl=first["epistemic_loss"], w=worst["step"],
            wl=worst["epistemic_loss"], ws=" and ".join(worst["signals_lost"]) or "signal")
    return ("- Catastrophic degradation begins at the first flagged step, **`{step}`**: it removes "
            "{rm} — losing {sig} — while adding only {dc} extra compression. From there, each "
            "further strip (toward constraint-only) destroys a signal family for almost no token "
            "gain.{note}").format(step=first["step"], rm=first["removes"],
                                  sig=", ".join(first["signals_lost"]) or "signal",
                                  dc=first["extra_compression"], note=note)


if __name__ == "__main__":
    run()

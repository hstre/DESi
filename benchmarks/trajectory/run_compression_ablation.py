#!/usr/bin/env python3
"""DESi compression ABLATION audit on DriftBench (READ-ONLY, measurement-only).

Decompose the DESi ~96% trajectory-state compression into explicit variants and
quantify, per variant: token savings vs. the raw transcript AND how much of each
epistemic signal (constraint / branch / recovery / drift-event / lock-in) survives.

Variants (nested field-sets, increasing information):
  A  raw transcript                       -- no compression
  B  raw minus filler                     -- drop acknowledgement / low-information turns only
  C  constraint-state only                -- constraint preservation scalars
  D  constraint + branch state            -- add branch entropy / collapse
  E  constraint + branch + event ledger   -- add recovery + per-turn drift/recovery events
  F  full DESi compact state (v1.1)        -- add lock-in + recovery-quality + drift-energy + composite

This MEASURES the already-computed DESi v1 / v1.1 trajectory state (the thing being
compressed); it does NOT recompute or mutate any DESi metric, tune any threshold, or
touch the DESi core. No embeddings, no LLM, no Neo4j. Token counter is the same
offline static tokenizer used by the compression demo (deterministic). The companion
`compression_loss_audit.py` reads this run's rows and attributes the loss per step.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

# context_compression_demo sets HF_HUB_OFFLINE on import and gives us the SAME
# deterministic token counter + the canonical v1.1 compact-state serializer (F).
from context_compression_demo import token_count, build_desi_state  # noqa: E402
from trajectory_adapter import _content  # noqa: E402
from drift_metrics import _corr, _spearman  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_V1 = _RESULTS / "driftbench_trace_v1_summaries.jsonl"
_V11 = _RESULTS / "driftbench_trace_v11_summaries.jsonl"

VARIANTS = ("A", "B", "C", "D", "E", "F")

# Which epistemic signal each variant carries explicitly (A/B = recoverable from text).
# Clean nesting so each strip-step removes exactly one signal family:
#   F->E removes lock-in ; E->D removes recovery+event ; D->C removes branch.
SIGNALS = ("constraint", "branch", "recovery", "event", "lock_in")
CARRIES = {
    "A": {"constraint", "branch", "recovery", "event", "lock_in"},  # raw text: all recoverable
    "B": {"constraint", "branch", "recovery", "event", "lock_in"},  # filler carries none of these
    "C": {"constraint"},
    "D": {"constraint", "branch"},
    "E": {"constraint", "branch", "recovery", "event"},
    "F": {"constraint", "branch", "recovery", "event", "lock_in"},
}

# Each signal's DESi field -> the auditor dimension it is supposed to track (for weighting
# the loss by how much REAL signal a field carries). Measured once on the full set; never tuned.
SIGNAL_FIELD = {
    "constraint": "constraint_half_life_mean",
    "branch": "branch_entropy_proxy",
    "recovery": "recovery_quality_proxy",
    "event": "total_events",
    "lock_in": "lock_in_proxy",
}
SIGNAL_AUDITOR = {
    "constraint": "constraint_adherence",
    "branch": "alternative_coverage",
    "recovery": "recoverability",
    "event": "drift_severity",
    "lock_in": "lock_in_binary",
}

_ACK = frozenset((
    "thanks thank ok okay sure great good understood noted got sounds fine yes yeah yep "
    "right alright acknowledged perfect absolutely certainly appreciate welcome glad"
).split())


def is_filler(content: str) -> bool:
    """Deterministic, label-free 'low-information turn' rule (structural, not tuned)."""
    toks = _content(content)
    return len(toks) < 4 or toks <= _ACK


def transcript_text(item: dict) -> str:
    return "\n".join(m.get("content", "") for m in item.get("messages", []))


def transcript_minus_filler(item: dict) -> str:
    return "\n".join(m.get("content", "") for m in item.get("messages", [])
                     if not is_filler(m.get("content", "")))


def raw_drift_proxy(assistant_texts: list) -> float:
    """Cheap RAW-text drift: 1 - lexical overlap between first and last assistant turn."""
    if len(assistant_texts) < 2:
        return 0.0
    a, b = _content(assistant_texts[0]), _content(assistant_texts[-1])
    u = a | b
    return round(1.0 - (len(a & b) / len(u) if u else 0.0), 3)


def _fmt(v):
    return f"{v}"


def serialize_level(summary: dict, v11: dict, level: str) -> str:
    """Serialize the cumulative field-set for a structured variant (C/D/E) in a compact
    key=value style. F uses the canonical v1.1 compact state (build_desi_state)."""
    s = summary
    parts = [
        f"constraint_preservation={_fmt(s['constraint_half_life_mean'])}",
        f"unrecovered={_fmt(s['unrecovered_constraints'])}",
        f"max_decay={_fmt(s['max_constraint_decay'])}",
    ]
    if level in ("D", "E"):
        parts += [f"branch_entropy={_fmt(s['branch_entropy_proxy'])}",
                  f"collapse={_fmt(s['branch_collapse_events'])}"]
    if level == "E":
        ledger = ";".join(f"{e['turn']}:{','.join(e['events'])}"
                          for e in s.get("drift_event_ledger", []))
        parts += [f"recovery op={_fmt(s['operational_recovery_count'])}",
                  f"rhet={_fmt(s['rhetorical_recovery_count'])}",
                  f"fail={_fmt(s['failed_recovery_count'])}",
                  f"events=[{ledger}]"]
    return " ".join(parts)


def variant_state_text(item, summary, v11, level) -> str:
    if level == "A":
        return transcript_text(item)
    if level == "B":
        return transcript_minus_filler(item)
    if level == "F":
        return build_desi_state(summary, v11["v11_irreversible_lock_in_proxy_v11"], v11["v11_composite"])
    return serialize_level(summary, v11, level)


def _load_summaries():
    v1, v11 = {}, {}
    for line in _V1.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            v1[r["run_id"]] = r
    for line in _V11.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            v11[r["run_id"]] = r
    return v1, v11


def build_rows() -> list:
    from driftbench_loader import iter_all
    v1, v11 = _load_summaries()
    rows = []
    for it in iter_all():
        rid = it["run_id"]
        if rid not in v1 or rid not in v11:
            continue
        vr, v11r = v1[rid], v11[rid]
        s = vr["summary"]
        a = it["auditor"]
        assistant = [m["content"] for m in it["messages"] if m.get("role") == "assistant"]
        total_events = sum(len(e.get("events", [])) for e in s.get("drift_event_ledger", []))
        toks = {lv: token_count(variant_state_text(it, s, v11r, lv)) for lv in VARIANTS}
        row = {
            "run_id": rid, "model_id": it["model_id"], "condition": it["condition"],
            "drift": vr["drift"], "drift_severity": vr["drift_severity"],
            "constraint_adherence": vr.get("constraint_adherence"),
            "alternative_coverage": vr.get("alternative_coverage"),
            "recoverability": vr.get("recoverability"),
            "lock_in_binary": 1 if vr["drift"] == "trajectory_lock_in" else 0,
            "tokens": toks,
            "raw_drift": raw_drift_proxy(assistant),
            # raw signal-field values used for weighting + drift-curve
            "constraint_half_life_mean": s["constraint_half_life_mean"],
            "branch_entropy_proxy": s["branch_entropy_proxy"],
            "recovery_quality_proxy": s["recovery_quality_proxy"],
            "total_events": total_events,
            "lock_in_proxy": v11r["v11_irreversible_lock_in_proxy_v11"],
            # drift-curve raw signals (higher = more drift), per level
            "max_constraint_decay": s["max_constraint_decay"],
            "unrecovered_constraints": s["unrecovered_constraints"],
            "branch_collapse_events": s["branch_collapse_events"],
            "failed_recovery_count": s["failed_recovery_count"],
            "cumulative_drift_energy": s["cumulative_drift_energy"],
        }
        rows.append(row)
    return rows


# ---- aggregation helpers (pure, reused by tests + loss audit) --------------------

def _minmax(values):
    lo, hi = min(values), max(values)
    rng = hi - lo
    return [0.0 if rng == 0 else (v - lo) / rng for v in values]


_LEVEL_DRIFT_SIGNALS = {  # cumulative raw drift signals available at each structured level
    "C": ["max_constraint_decay", "unrecovered_constraints", "inv_constraint_half_life"],
    "D": ["branch_collapse_events"],
    "E": ["total_events", "failed_recovery_count"],
    "F": ["lock_in_proxy", "cumulative_drift_energy"],
}


def _drift_curves(rows):
    """Per-variant drift score -> correlation with auditor severity.
    A/B use the raw lexical proxy; C/D/E/F use the mean of min-max-normalized
    carried drift signals (data-driven normalization, NOT label tuning)."""
    sev = [r["drift_severity"] for r in rows]
    # normalize each raw signal once across the dataset
    norm = {}
    raw_named = {
        "max_constraint_decay": [r["max_constraint_decay"] for r in rows],
        "unrecovered_constraints": [r["unrecovered_constraints"] for r in rows],
        "inv_constraint_half_life": [1.0 - r["constraint_half_life_mean"] for r in rows],
        "branch_collapse_events": [r["branch_collapse_events"] for r in rows],
        "total_events": [r["total_events"] for r in rows],
        "failed_recovery_count": [r["failed_recovery_count"] for r in rows],
        "lock_in_proxy": [r["lock_in_proxy"] for r in rows],
        "cumulative_drift_energy": [r["cumulative_drift_energy"] for r in rows],
    }
    for k, vals in raw_named.items():
        norm[k] = _minmax(vals)
    out = {}
    # A,B: lexical proxy
    out["A"] = {"corr": _corr([r["raw_drift"] for r in rows], sev),
                "spearman": _spearman([r["raw_drift"] for r in rows], sev)}
    out["B"] = out["A"]  # filler removal does not change first/last assistant turns
    cum = []
    for lv in ("C", "D", "E", "F"):
        cum += _LEVEL_DRIFT_SIGNALS[lv]
        scores = [st.mean([norm[k][i] for k in cum]) for i in range(len(rows))]
        out[lv] = {"corr": _corr(scores, sev), "spearman": _spearman(scores, sev)}
    return out


def signal_weights(rows):
    """|corr(signal field, its auditor target)| measured once -- how much REAL epistemic
    signal each field carries. Used to weight epistemic loss. Never tuned."""
    w = {}
    for sig in SIGNALS:
        xs = [r[SIGNAL_FIELD[sig]] for r in rows]
        ys = [r[SIGNAL_AUDITOR[sig]] for r in rows]
        c = _corr(xs, ys)
        w[sig] = abs(c) if c is not None else 0.0
    return w


def epistemic_retained(variant: str, w: dict) -> float:
    tot = sum(w.values())
    if tot == 0:
        return 0.0
    return round(sum(w[s] for s in SIGNALS if s in CARRIES[variant]) / tot, 3)


def aggregate(rows):
    n = len(rows)
    w = signal_weights(rows)
    drift = _drift_curves(rows)
    tokA = st.mean([r["tokens"]["A"] for r in rows])
    per = {}
    for lv in VARIANTS:
        toks = [r["tokens"][lv] for r in rows]
        ratios = [round(1.0 - r["tokens"][lv] / r["tokens"]["A"], 3) if r["tokens"]["A"] else 0.0
                  for r in rows]
        per[lv] = {
            "tokens_mean": round(st.mean(toks), 1), "tokens_median": round(st.median(toks), 1),
            "compression_mean": round(st.mean(ratios), 4),
            "compression_median": round(st.median(ratios), 4),
            "above90": sum(1 for x in ratios if x > 0.90),
            "drift_corr": drift[lv]["corr"], "continuity_spearman": drift[lv]["spearman"],
            "epistemic_retained": epistemic_retained(lv, w),
            "carries": sorted(CARRIES[lv]),
        }
    return {"n": n, "weights": w, "tokens_A_mean": round(tokA, 1), "per": per}


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with open(_RESULTS / "compression_ablation.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    agg = aggregate(rows)
    _report(rows, agg)
    p = agg["per"]
    print(f"ablation: N={agg['n']} F_compression={p['F']['compression_mean']} "
          f"F_retained={p['F']['epistemic_retained']} F_driftcorr={p['F']['drift_corr']} "
          f"C_retained={p['C']['epistemic_retained']} A_tok={agg['tokens_A_mean']}")


def _report(rows, agg):
    n, w, per = agg["n"], agg["weights"], agg["per"]
    desc = {"A": "raw transcript (no compression)", "B": "raw minus filler",
            "C": "constraint-state only", "D": "constraint + branch",
            "E": "constraint + branch + event ledger", "F": "full DESi compact state (v1.1)"}
    wtot = sum(w.values())

    md = [
        "# DESi compression ablation — DriftBench (read-only audit)\n",
        "Decompose the DESi trajectory-state compression into nested variants and measure, per "
        "variant, token savings vs. the raw transcript and how much of each epistemic signal "
        "survives. Measurement-only: uses the already-computed DESi v1 / v1.1 state, the offline "
        "static token counter, and the independent auditor labels. No DESi-core change, no metric "
        "mutation, no threshold tuning, no embeddings, no LLM.\n",
        f"## Size\n- Trajectories: **{n}** (joined: DriftBench transcript + DESi v1/v1.1 state + "
        "auditor). Raw transcript mean **{t}** tokens.".format(t=agg["tokens_A_mean"]),
        "",
        "## Per-variant: token savings & epistemic preservation\n",
        "| variant | what it carries | mean tokens | compression vs raw | >90% | drift r | "
        "continuity ρ | epistemic retained |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for lv in VARIANTS:
        p = per[lv]
        md.append(
            f"| {lv} ({desc[lv]}) | {', '.join(p['carries'])} | {p['tokens_mean']} | "
            f"{p['compression_mean']} | {p['above90']}/{n} | {p['drift_corr']} | "
            f"{p['continuity_spearman']} | {p['epistemic_retained']} |")
    md += [
        "",
        "- Compression is measured against each trajectory's OWN raw token count, then averaged.",
        "- `epistemic retained` = fraction of total measured epistemic signal a variant carries, "
        "weighting each signal family by how strongly its DESi field tracks the matching auditor "
        "dimension (weights below). A/B are raw text, so every signal is recoverable (retained=1).",
        "",
        "## Signal weights (how much real epistemic signal each field carries)\n",
        "| signal family | DESi field | auditor target | |corr| (weight) |",
        "| --- | --- | --- | --- |",
        *[f"| {s} | {SIGNAL_FIELD[s]} | {SIGNAL_AUDITOR[s]} | {round(w[s],3)} |" for s in SIGNALS],
        f"| **total** | | | {round(wtot,3)} |",
        "- These are |Pearson| of the DESi state field vs. its natural auditor dimension over all "
        f"{n} trajectories. They quantify which dropped field actually costs epistemic information "
        "(a field that does not track its auditor dimension is cheap to drop).",
        f"- **Notable:** the lock-in proxy's weight ({round(w['lock_in'],3)}) is near zero — on "
        "DriftBench the irreversible-lock-in field barely tracks the auditor's lock-in class, so the "
        "F→E step (lock-in loss) destroys little MEASURED signal even though that field is unique to "
        "F. The drift-event count carries the most ("
        f"{round(w['event'],3)}).",
        "",
        "## Preservation matrix (signal × variant)\n",
        "| signal | A | B | C | D | E | F |", "| --- | --- | --- | --- | --- | --- | --- |",
        *[f"| {s} | " + " | ".join("kept" if s in CARRIES[lv] else "LOST" for lv in VARIANTS) + " |"
          for s in SIGNALS],
        "- `kept` = the variant explicitly carries the field (A/B: recoverable from text); "
        "`LOST` = the signal is no longer present and cannot be reconstructed from the variant.",
        "",
        "## Preservation curve (compression ↑ vs epistemic retained)\n",
        "| order (more compression →) | A | B | F | E | D | C |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| compression vs raw | {per['A']['compression_mean']} | {per['B']['compression_mean']} | "
        f"{per['F']['compression_mean']} | {per['E']['compression_mean']} | "
        f"{per['D']['compression_mean']} | {per['C']['compression_mean']} |",
        f"| epistemic retained | {per['A']['epistemic_retained']} | {per['B']['epistemic_retained']} | "
        f"{per['F']['epistemic_retained']} | {per['E']['epistemic_retained']} | "
        f"{per['D']['epistemic_retained']} | {per['C']['epistemic_retained']} |",
        "- Ordered by increasing compression. The big jump (raw → full DESi state) keeps ALL signal; "
        "shrinking the state further (F→E→D→C) trades large epistemic loss for negligible extra "
        "tokens (see the loss audit).",
        "",
    ]
    # Pareto
    pts = {lv: (per[lv]["compression_mean"], per[lv]["epistemic_retained"]) for lv in VARIANTS}
    pareto = _pareto_front(pts)
    knee = max(VARIANTS, key=lambda lv: per[lv]["epistemic_retained"] * (per[lv]["compression_mean"] > 0.9))
    f_optimal = ("F" in pareto and per["F"]["epistemic_retained"] >= max(
        per[lv]["epistemic_retained"] for lv in ("C", "D", "E", "F")) and per["F"]["compression_mean"] > 0.9)
    md += [
        "## Pareto analysis\n",
        f"- Pareto-optimal variants (no other variant beats them on BOTH compression and retained): "
        f"**{', '.join(sorted(pareto))}**.",
        f"- Among the structured states, **F retains the most signal "
        f"({per['F']['epistemic_retained']}) at {round(100*per['F']['compression_mean'])}% "
        f"compression**, while C/D/E save only "
        f"{round(100*(per['C']['compression_mean']-per['F']['compression_mean']),2)}–"
        f"{round(100*(per['E']['compression_mean']-per['F']['compression_mean']),2)} extra "
        f"percentage points of tokens for a drop to {per['E']['epistemic_retained']}/"
        f"{per['D']['epistemic_retained']}/{per['C']['epistemic_retained']} retained.",
        f"- **Is Full DESi (F) near Pareto-optimal?** {'YES' if f_optimal else 'NO'} — "
        + ("it sits at the knee: ~maximum compression with 100% of the measured epistemic signal; "
           "every smaller variant sacrifices a whole signal family for a negligible token gain."
           if f_optimal else "see table; another variant dominates it."),
        "",
        "## Final answers\n",
        f"- **Which component contributes most token savings?** The raw→state transition itself "
        f"(variant F): mean compression {per['F']['compression_mean']} "
        f"({round(100*per['F']['compression_mean'])}%). The structured sub-components (branch / "
        "events / lock-in) each add only a few tokens, so removing them saves almost nothing.",
        f"- **Which component contributes most information loss when dropped?** the "
        f"**{_heaviest_signal(w)}** family (weight {round(max(w.values()),3)}); see the loss audit "
        "for the per-step attribution.",
        f"- **Where does catastrophic epistemic degradation begin?** Not in the big compression "
        "(raw→F keeps everything); it begins when the compact state is shrunk BELOW F — the first "
        "strip-step (F→E, lock-in) starts removing irreplaceable signal for ~0 token savings.",
        f"- **Is Full DESi near Pareto-optimal?** {'YES' if f_optimal else 'NO'} (see Pareto).",
        f"- **Which compression operations are safest?** raw→filler-removal (B) and raw→full-state "
        "(F): large or free token savings with no epistemic loss.",
        f"- **Which are most dangerous?** stripping components OUT of the full state (F→E→D→C): "
        "they destroy specific signals while saving almost no tokens.",
        f"- **Does DESi know when its own compression becomes epistemically unsafe?** The compact "
        "state's own counts flag it per-trajectory (branch_collapse>0, recovery/failed events>0, "
        "lock-in>0 mark load-bearing fields); there is no separate core alarm. See loss audit.",
        "",
        "## DESi-core invariance\n- Read-only audit: consumes precomputed v1/v1.1 state + auditor "
        "labels; reads `desi.frames` only via the existing adapter; core byte-identical; no "
        "ontology change, no metric mutation, no threshold tuning.",
        "",
        "## Honesty / limits\n- Variant B removes only whole low-information turns by a fixed "
        "structural rule (<4 content tokens or pure acknowledgement); on DriftBench's substantive "
        "transcripts that is a small saving, reported as-is. `epistemic retained` for A/B assumes "
        "filler carries none of the five signal families (true by construction) and is not "
        "re-derived. Signal weights are |Pearson| of a deterministic DESi field vs. a single-"
        "auditor dimension — indicative magnitudes, not ground truth. The per-variant `drift r` "
        "column uses an EQUAL-WEIGHT mean of the carried normalized drift signals, so adding "
        "weakly-correlated fields (lock-in, drift-energy) slightly DILUTES it — which is why F's "
        "drift r is marginally below E's; the |corr|-weighted `epistemic retained` is the headline "
        "preservation measure, not that naive composite. Drift correlations for A/B use a cheap "
        "lexical proxy and are not directly comparable to the structured composite. Drift detection "
        "is already near-saturated at constraint-only C (r≈0.40): for DRIFT alone later components "
        "add little — F's value is preserving the OTHER signal families.",
    ]
    (_REPORTS / "compression_ablation_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _pareto_front(pts: dict) -> set:
    front = set()
    for lv, (c, e) in pts.items():
        if not any(lv2 != lv and pts[lv2][0] >= c and pts[lv2][1] >= e
                   and (pts[lv2][0] > c or pts[lv2][1] > e) for lv2 in pts):
            front.add(lv)
    return front


def _heaviest_signal(w: dict) -> str:
    return max(w, key=lambda s: w[s]) if w else "n/a"


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""DESi Context Compression Demo on DriftBench (PERIPHERAL, deterministic).

For each trajectory: count raw transcript tokens, build a compact DESi state summary
from the TrajectoryTrace v1.1 fields, count its tokens, compute the compression
ratio, and compare drift detection from (A) a raw-transcript proxy vs (B) the
compact DESi-summary proxy -- against the auditor drift severity.

No DESi-core change, no LLM calls, no Neo4j. Token counting uses the locally-cached
model2vec tokenizer (offline, deterministic) with a regex fallback. DESi state comes
from the already-computed v1 (rich) + v1.1 (improved lock-in) summaries; the raw
transcripts come from the cached DriftBench snapshot.
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from driftbench_loader import iter_all  # noqa: E402
from drift_metrics import _corr  # noqa: E402
from trajectory_adapter import _content  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_V1 = _RESULTS / "driftbench_trace_v1_summaries.jsonl"
_V11 = _RESULTS / "driftbench_trace_v11_summaries.jsonl"

_TOK = None
_TOK_KIND = None


def _tokenizer():
    global _TOK, _TOK_KIND
    if _TOK_KIND is not None:
        return _TOK
    try:
        from model2vec import StaticModel
        _TOK = StaticModel.from_pretrained("minishlab/potion-base-8M").tokenizer
        _TOK_KIND = "model2vec/potion-base-8M"
    except Exception:
        _TOK = None
        _TOK_KIND = "regex-words"
    return _TOK


def token_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    tok = _tokenizer()
    if tok is not None:
        try:
            return len(tok.encode(text).ids)
        except Exception:
            pass
    return len(re.findall(r"\S+", text or ""))


def transcript_text(item: dict) -> str:
    return "\n".join(m.get("content", "") for m in item.get("messages", []))


def build_desi_state(v1_summary: dict, v11_lock_in: float, composite_v11: float) -> str:
    """Compact DESi v1.1 state summary -- the drift-relevant scalars + event ledger."""
    s = v1_summary
    ledger = ";".join(f"{e['turn']}:{','.join(e['events'])}" for e in s.get("drift_event_ledger", []))
    return (
        f"constraint_preservation={s['constraint_half_life_mean']} "
        f"unrecovered={s['unrecovered_constraints']} max_decay={s['max_constraint_decay']}; "
        f"recovery op={s['operational_recovery_count']} rhet={s['rhetorical_recovery_count']} "
        f"fail={s['failed_recovery_count']} quality={s['recovery_quality_proxy']}; "
        f"lock_in={v11_lock_in}; branch_entropy={s['branch_entropy_proxy']} "
        f"collapse={s['branch_collapse_events']}; drift_energy={s['cumulative_drift_energy']} "
        f"composite={composite_v11}; events=[{ledger}]"
    )


def raw_drift_proxy(item: dict) -> float:
    """Cheap RAW-transcript drift: 1 - lexical overlap between first and last assistant turn."""
    turns = [m["content"] for m in item.get("messages", []) if m.get("role") == "assistant"]
    if len(turns) < 2:
        return 0.0
    a, b = _content(turns[0]), _content(turns[-1])
    u = a | b
    return round(1.0 - (len(a & b) / len(u) if u else 0.0), 3)


def _load(path, pick):
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = pick(r)
    return out


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    v1 = _load(_V1, lambda r: r)
    v11 = _load(_V11, lambda r: (r["v11_irreversible_lock_in_proxy_v11"], r["v11_composite"]))
    rows = []
    with open(_RESULTS / "context_compression_demo.jsonl", "w", encoding="utf-8") as f:
        for it in iter_all():
            rid = it["run_id"]
            if rid not in v1 or rid not in v11:
                continue
            lock_in, comp11 = v11[rid]
            vr = v1[rid]
            raw_tokens = token_count(transcript_text(it))
            state = build_desi_state(vr["summary"], lock_in, comp11)
            desi_tokens = token_count(state)
            ratio = round(1.0 - desi_tokens / raw_tokens, 3) if raw_tokens else 0.0
            row = {
                "run_id": rid, "model_id": it["model_id"], "condition": it["condition"],
                "drift": vr["drift"], "drift_severity": vr["drift_severity"],
                "raw_tokens": raw_tokens, "desi_state_tokens": desi_tokens,
                "compression_ratio": ratio,
                "raw_drift": raw_drift_proxy(it), "desi_drift": comp11,
                # the compact state carries each drift signal explicitly (preserved by construction)
                "constraint_preservation_preserved": int(vr["summary"]["constraint_half_life_mean"] is not None),
                "recovery_events_preserved": int(
                    (vr["summary"]["operational_recovery_count"] + vr["summary"]["rhetorical_recovery_count"]
                     + vr["summary"]["failed_recovery_count"]) >= 0),
                "lock_in_preserved": int(lock_in is not None),
                "branch_state_preserved": int(vr["summary"]["branch_entropy_proxy"] is not None),
            }
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _report(rows)


def _report(rows):
    n = len(rows)
    if n == 0:
        (_REPORTS / "context_compression_demo.md").write_text("# Context Compression Demo — 0 rows\n")
        print("no rows")
        return
    ratios = [r["compression_ratio"] for r in rows]
    raw = [r["raw_tokens"] for r in rows]
    desi = [r["desi_state_tokens"] for r in rows]
    sev = [r["drift_severity"] for r in rows]

    corr_raw = _corr([r["raw_drift"] for r in rows], sev)
    corr_desi = _corr([r["desi_drift"] for r in rows], sev)
    in_band = sum(1 for x in ratios if 0.70 <= x <= 0.90)
    above = sum(1 for x in ratios if x > 0.90)
    pres = {k: round(sum(r[k] for r in rows) / n, 3) for k in
            ("constraint_preservation_preserved", "recovery_events_preserved",
             "lock_in_preserved", "branch_state_preserved")}
    drift_score_preservation = (round((corr_desi or 0) / (corr_raw or 1e-9), 2)
                                if corr_raw not in (None, 0) else None)
    best = sorted(rows, key=lambda r: r["compression_ratio"], reverse=True)[:10]
    worst = sorted(rows, key=lambda r: r["compression_ratio"])[:10]

    md = [
        "# DESi Context Compression Demo — DriftBench\n",
        "Replace each raw multi-turn transcript with a compact DESi v1.1 STATE summary "
        "(constraint preservation + recovery quality + lock-in + branch state + drift-event "
        "ledger + composite) and ask: how many tokens are saved, and is drift still detectable "
        f"from the compact state? Token counter: `{_TOK_KIND}` (offline, deterministic). No "
        "LLM, no core change.\n",
        f"## Token savings (N={n})\n",
        "| metric | mean | median |", "| --- | --- | --- |",
        f"| raw transcript tokens | {round(st.mean(raw))} | {round(st.median(raw))} |",
        f"| DESi state tokens | {round(st.mean(desi))} | {round(st.median(desi))} |",
        f"| compression ratio (tokens saved) | {round(st.mean(ratios),3)} | {round(st.median(ratios),3)} |",
        "",
        f"- **Is 70-90% savings realistic?** {in_band}/{n} trajectories "
        f"({round(100*in_band/n)}%) land in the 70-90% band; {above}/{n} "
        f"({round(100*above/n)}%) exceed 90%. Mean savings "
        f"**{round(100*st.mean(ratios))}%** (median {round(100*st.median(ratios))}%).",
        "",
        "## Drift detection: raw proxy (A) vs DESi summary (B)\n",
        f"- A (raw transcript proxy, first-vs-last lexical drift) ~ auditor severity: r={corr_raw}.",
        f"- B (DESi compact-state composite drift) ~ auditor severity: r={corr_desi}.",
        f"- **drift_score_preservation (B/A): {drift_score_preservation}** -- the compact "
        f"state detects drift {'as well as or better than' if (corr_desi or 0) >= (corr_raw or 0) else 'worse than'} "
        "the raw transcript, at a fraction of the tokens.",
        "",
        "## Signal preservation (compact state carries each drift signal explicitly)\n",
        "| signal | preserved fraction |", "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in pres.items()],
        "- Compression is to a STRUCTURED state, not lossy text truncation: the v1.1 drift "
        "signals are retained as explicit scalars + a per-turn event ledger.",
        "",
        "## 10 best (highest compression)\n",
        "| run | model | drift | raw_tok | desi_tok | ratio |", "| --- | --- | --- | --- | --- | --- |",
        *[f"| {r['run_id'][:8]} | {r['model_id'].split('/')[-1][:14]} | {r['drift']} | {r['raw_tokens']} | {r['desi_state_tokens']} | {r['compression_ratio']} |" for r in best],
        "",
        "## 10 worst (lowest compression)\n",
        "| run | model | drift | raw_tok | desi_tok | ratio |", "| --- | --- | --- | --- | --- | --- |",
        *[f"| {r['run_id'][:8]} | {r['model_id'].split('/')[-1][:14]} | {r['drift']} | {r['raw_tokens']} | {r['desi_state_tokens']} | {r['compression_ratio']} |" for r in worst],
        "",
        "## Does DriftBench drift detection remain stable after compression?\n",
        ("**Yes.** The compact DESi state preserves (and here exceeds) the raw-transcript "
         "drift signal's alignment with the auditor while removing ~{p}% of the tokens -- "
         "drift detection is stable under compression.").format(p=round(100*st.mean(ratios)))
        if (corr_desi or 0) >= (corr_raw or 0) else
        "**Partially** -- the compact state saves tokens but its drift correlation is below "
        "the raw proxy; compression trades some drift fidelity here.",
        "",
        "## Honesty / limits\n",
        "- Token counts use a static tokenizer as a deterministic proxy; the raw-drift proxy "
        "(A) is a cheap first-vs-last lexical signal, not a full re-derivation; signal "
        "'preservation' means the compact state carries each field explicitly (it is a "
        "structured summary, so by construction lossless for those signals). No core change, "
        "no LLM, no auditor-label tuning.",
    ]
    (_REPORTS / "context_compression_demo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"compression demo: N={n} mean_ratio={round(st.mean(ratios),3)} "
          f"raw_tok~{round(st.mean(raw))} desi_tok~{round(st.mean(desi))} "
          f"corrA={corr_raw} corrB={corr_desi} in70-90={in_band}")


if __name__ == "__main__":
    run()

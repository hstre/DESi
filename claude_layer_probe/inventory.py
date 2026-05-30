"""Unify the four token-pair sources into one transparent table, KEEPING the state_type.

Each row gets:
  artifact_path, source_branch, sample_id, raw_tokens, state_tokens, compression_ratio,
  savings (= raw - state, in tokens), state_type.

state_type values:
  - wiki_compact_state_v1    : single-layer DESi-style compact state (wikipedia_v1)
  - wiki_dual_layer_anchors  : dual-layer ACTIVE anchor map over cold prose (wikipedia_dual)
  - wiki_dual_layer_v2       : v2 composite-anchor refinement (wikipedia_dual_v2)
  - driftbench_state_summary : DriftBench-trajectory compact state (driftbench)

These are NOT averaged together by default — that would conflate systems.
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics as st
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DATA = _HERE / "data_inventory"

SOURCES = (
    {"path": _DATA / "wikipedia_v1.jsonl",
     "branch": "desi-wikipedia-epistemic-compression-probe",
     "state_col": "desi_state_tokens", "id_col": "pageid", "state_type": "wiki_compact_state_v1"},
    {"path": _DATA / "wikipedia_dual.jsonl",
     "branch": "desi-wikipedia-dual-layer-probe",
     "state_col": "state_tokens", "id_col": "pageid", "state_type": "wiki_dual_layer_anchors"},
    {"path": _DATA / "wikipedia_dual_v2.jsonl",
     "branch": "desi-wikipedia-dual-layer-v2",
     "state_col": "state_tokens", "id_col": "pageid", "state_type": "wiki_dual_layer_v2"},
    {"path": _DATA / "driftbench_compression.jsonl",
     "branch": "desi-context-compression-demo",
     "state_col": "desi_state_tokens", "id_col": "run_id",
     "state_type": "driftbench_state_summary"},
)


def _rows():
    out = []
    for src in SOURCES:
        if not src["path"].exists():
            continue
        sha = hashlib.sha256(src["path"].read_bytes()).hexdigest()[:16]
        for line in src["path"].read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            raw = int(d.get("raw_tokens") or 0)
            state = int(d.get(src["state_col"]) or 0)
            if raw <= 0:
                continue
            out.append({
                "artifact_path": str(src["path"].relative_to(_HERE.parent)),
                "source_branch": src["branch"],
                "source_sha16": sha,
                "sample_id": str(d.get(src["id_col"])),
                "raw_tokens": raw,
                "state_tokens": state,
                "compression_ratio": round(1.0 - state / raw, 4),
                "savings_tokens": raw - state,
                "state_type": src["state_type"],
            })
    return out


def _pearson(xs, ys):
    if len(xs) < 3:
        return None
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return None
    return round(sxy / (sxx ** 0.5 * syy ** 0.5), 4)


BINS = ((0, 1000, "<1k"), (1000, 5000, "1k-5k"), (5000, 10000, "5k-10k"),
        (10000, 50000, "10k-50k"), (50000, float("inf"), ">=50k"))


def _per_bin(rows):
    out = []
    for lo, hi, label in BINS:
        sub = [r for r in rows if lo <= r["raw_tokens"] < hi]
        if not sub:
            out.append({"bin": label, "n": 0, "note": "no samples in this bin"})
            continue
        out.append({
            "bin": label, "n": len(sub),
            "mean_raw": round(st.mean(r["raw_tokens"] for r in sub)),
            "mean_state": round(st.mean(r["state_tokens"] for r in sub)),
            "mean_savings": round(st.mean(r["savings_tokens"] for r in sub)),
            "median_savings": round(st.median(r["savings_tokens"] for r in sub)),
            "mean_compression_ratio": round(st.mean(r["compression_ratio"] for r in sub), 4),
        })
    return out


def _stats(rows, label):
    raw = [r["raw_tokens"] for r in rows]
    state = [r["state_tokens"] for r in rows]
    savings = [r["savings_tokens"] for r in rows]
    return {
        "label": label, "n": len(rows),
        "raw_mean": round(st.mean(raw)) if raw else 0,
        "raw_median": round(st.median(raw)) if raw else 0,
        "raw_min": min(raw) if raw else 0,
        "raw_max": max(raw) if raw else 0,
        "state_mean": round(st.mean(state)) if state else 0,
        "state_median": round(st.median(state)) if state else 0,
        "savings_mean": round(st.mean(savings)) if savings else 0,
        "savings_median": round(st.median(savings)) if savings else 0,
        "savings_min": min(savings) if savings else 0,
        "savings_max": max(savings) if savings else 0,
        "corr_raw_vs_savings": _pearson(raw, savings) if len(rows) >= 3 else None,
        "corr_raw_vs_state":   _pearson(raw, state) if len(rows) >= 3 else None,
    }


def collect() -> dict:
    rows = _rows()
    by_type = {}
    for r in rows:
        by_type.setdefault(r["state_type"], []).append(r)
    return {
        "all_rows": rows,
        "overall": _stats(rows, "ALL (mixed state_types; see honest caveat)"),
        "per_state_type": {k: _stats(v, k) for k, v in by_type.items()},
        "per_state_type_bins": {k: _per_bin(v) for k, v in by_type.items()},
        "overall_bins": _per_bin(rows),
        "sources": [{"path": str(s["path"].relative_to(_HERE.parent)),
                     "branch": s["branch"],
                     "sha16": hashlib.sha256(s["path"].read_bytes()).hexdigest()[:16]
                     if s["path"].exists() else None,
                     "state_type": s["state_type"]} for s in SOURCES],
    }


def write_csv(rows, path):
    if not rows:
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    summary = collect()
    write_csv(summary["all_rows"], _HERE / "results" / "inventory.csv")
    print(f"rows: {len(summary['all_rows'])}; per-type: " +
          ", ".join(f"{k}={v['n']}" for k, v in summary["per_state_type"].items()))

#!/usr/bin/env python3
"""DriftBench loader (PERIPHERAL, read-only).

DriftBench (driftbench/DriftBench on the HF hub, CC-BY-4.0) measures DRIFT in
multi-turn LLM-assisted scientific ideation: each item is a structured research
brief (objective + hard_constraints + banned_moves + success_criteria +
plausible_directions), a multi-turn transcript where the model is iteratively
pressured, and an independent AUDITOR score with DESi-relevant dimensions
(objective_fidelity, constraint_adherence, alternative_coverage,
complexity_inflation, recoverability) plus a drift_classification.

This loader downloads only the files needed for a small probe (briefs +
transcripts + matching auditor scores) and parses them. No model calls. It does
not modify the DESi core.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

REPO = "driftbench/DriftBench"
DRIFT_SEVERITY = {"no_drift": 0, "mild_drift": 1, "trajectory_drift": 2, "trajectory_lock_in": 3}
AUDITOR_DIMS = ("objective_fidelity", "constraint_adherence", "alternative_coverage",
                "complexity_inflation", "recoverability")


def _dl(filename: str) -> str:
    from huggingface_hub import hf_hub_download
    return hf_hub_download(REPO, filename, repo_type="dataset")


@lru_cache(maxsize=1)
def _siblings() -> tuple:
    from huggingface_hub import HfApi
    return tuple(s.rfilename for s in HfApi().dataset_info(REPO).siblings)


def parse_transcript(line: str) -> tuple[dict, list]:
    """Pure: one transcript JSONL line -> (metadata, messages)."""
    obj = json.loads(line)
    return obj.get("metadata", {}), obj.get("messages", [])


def auditor_severity(drift_classification: str) -> int:
    """Pure: map a drift_classification label to an ordinal severity (0..3)."""
    return DRIFT_SEVERITY.get(str(drift_classification), -1)


def load_briefs(brief_ids=None) -> dict:
    import yaml
    files = [f for f in _siblings() if f.startswith("briefs/") and f.endswith(".yaml")]
    out = {}
    for f in files:
        bid = os.path.splitext(os.path.basename(f))[0]
        if brief_ids is not None and bid not in brief_ids:
            continue
        out[bid] = yaml.safe_load(open(_dl(f), encoding="utf-8"))
    return out


def _auditor_for(run_id: str) -> dict | None:
    path = f"scores/auditor_{run_id}.jsonl"
    if path not in _siblings():
        return None
    for line in open(_dl(path), encoding="utf-8"):
        if line.strip():
            return json.loads(line)  # first (primary) auditor record
    return None


def load_sample(limit: int = 15, condition: str | None = None) -> list:
    """Download the first `limit` transcripts (optionally filtered by condition)
    that have a matching auditor score, attach the brief, and return items."""
    sibs = _siblings()
    tfiles = sorted(f for f in sibs if f.startswith("transcripts/") and f.endswith(".jsonl"))
    staged, needed = [], set()
    for tf in tfiles:
        if len(staged) >= limit:
            break
        run_id = os.path.basename(tf).split("_")[0]
        meta, msgs = parse_transcript(open(_dl(tf), encoding="utf-8").readline())
        if condition and meta.get("condition") != condition:
            continue
        aud = _auditor_for(run_id)
        if aud is None:
            continue
        needed.add(meta.get("brief_id"))
        staged.append((meta, msgs, aud))
    briefs = load_briefs(needed)
    out = []
    for meta, msgs, aud in staged:
        if meta.get("brief_id") in briefs:
            out.append({"run_id": meta.get("run_id"), "brief_id": meta.get("brief_id"),
                        "model_id": meta.get("model_id"), "condition": meta.get("condition"),
                        "brief": briefs[meta["brief_id"]], "messages": msgs, "auditor": aud})
    return out


def _snapshot_main() -> str:
    """Download the MAIN labelled set (briefs + transcripts + auditor scores) in one
    batched snapshot. Returns the local cache dir."""
    from huggingface_hub import snapshot_download
    return snapshot_download(
        REPO, repo_type="dataset",
        allow_patterns=["briefs/*.yaml", "transcripts/*.jsonl", "scores/auditor_*.jsonl"],
        max_workers=8,
    )


def iter_all():
    """Yield every MAIN-set item that has both a transcript and an auditor score.
    Streams (does not keep all messages in memory at once)."""
    import glob
    import yaml
    root = _snapshot_main()
    briefs = {os.path.splitext(os.path.basename(f))[0]: yaml.safe_load(open(f, encoding="utf-8"))
              for f in glob.glob(os.path.join(root, "briefs", "*.yaml"))}
    by_run = {}
    for tf in glob.glob(os.path.join(root, "transcripts", "*.jsonl")):
        by_run[os.path.basename(tf).split("_")[0]] = tf
    for af in sorted(glob.glob(os.path.join(root, "scores", "auditor_*.jsonl"))):
        run_id = os.path.basename(af)[len("auditor_"):-len(".jsonl")]
        tf = by_run.get(run_id)
        if tf is None:
            continue
        with open(af, encoding="utf-8") as fh:
            line = next((l for l in fh if l.strip()), None)
        if line is None:
            continue
        aud = json.loads(line)
        meta, msgs = parse_transcript(open(tf, encoding="utf-8").readline())
        bid = meta.get("brief_id")
        if bid not in briefs:
            continue
        yield {"run_id": meta.get("run_id"), "brief_id": bid, "model_id": meta.get("model_id"),
               "condition": meta.get("condition"), "brief": briefs[bid],
               "messages": msgs, "auditor": aud}


if __name__ == "__main__":
    sample = load_sample(5)
    print(f"loaded {len(sample)} items")
    for it in sample:
        a = it["auditor"]
        print(f"  {it['run_id']} brief={it['brief_id']} cond={it['condition']} "
              f"turns={sum(1 for m in it['messages'] if m['role']=='assistant')} "
              f"drift={a.get('drift_classification')} constraints={len(it['brief'].get('hard_constraints', []))}")

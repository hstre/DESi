#!/usr/bin/env python3
"""Topic-shift adapter for DeepDialogue (PERIPHERAL, deterministic).

Builds abrupt-topic-switch trajectories by stitching multi-turn dialogues from
DIFFERENT domains; the domain-boundary turns are exact, label-free ground-truth
shift points. Computes per-turn topic-continuity / discontinuity / frame signals
deterministically. No embeddings, no LLM semantic judging, no DESi-core change
(reads the DESi frame layer read-only via trajectory_adapter).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_adapter import _content, _frame  # noqa: E402

REPO = "SALT-Research/DeepDialogue-xtts"


def _snapshot() -> str:
    from huggingface_hub import snapshot_download
    return snapshot_download(REPO, repo_type="dataset",
                             allow_patterns=["data/dialogues_*/*.json"], max_workers=8)


def load_dialogues_by_domain(min_turns: int = 6) -> dict:
    """Return {domain: [dialogue, ...]} (sorted, deterministic) from the cached snapshot."""
    import glob
    root = _snapshot()
    by_dom: dict = {}
    for fp in sorted(glob.glob(os.path.join(root, "data", "dialogues_*", "*.json"))):
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        conv = d.get("conversation") or []
        dom = d.get("domain")
        if not dom or len(conv) < min_turns:
            continue
        by_dom.setdefault(dom, []).append({"id": os.path.splitext(os.path.basename(fp))[0],
                                           "domain": dom, "conversation": conv})
    for dom in by_dom:
        by_dom[dom].sort(key=lambda x: x["id"])
    return by_dom


def build_trajectories(by_domain: dict, n_traj: int, segs_per: int = 3, turns_per: int = 6) -> list:
    """Deterministically stitch dialogues from distinct domains into topic-switch
    trajectories. Shift boundaries = the turn indices where a new domain begins."""
    domains = sorted(by_domain)
    D = len(domains)
    trajs = []
    for i in range(n_traj):
        chosen = [domains[(i + j) % D] for j in range(segs_per)]
        if len(set(chosen)) < segs_per:        # need distinct domains
            continue
        turns, boundaries, seg = [], [], 0
        ok = True
        for dom in chosen:
            dl = by_domain[dom]
            dlg = dl[(i // D) % len(dl)]
            conv = dlg["conversation"][:turns_per]
            if len(conv) < 2:
                ok = False
                break
            if seg > 0:
                boundaries.append(len(turns))
            for u in conv:
                turns.append({"text": str(u.get("text", "")), "speaker": str(u.get("speaker", "")),
                              "segment": seg, "domain": dom})
            seg += 1
        if ok and len(turns) >= 4 and boundaries:
            trajs.append({"traj_id": f"ts-{i:04d}", "turns": turns,
                          "shift_boundaries": boundaries, "domains": chosen})
    return trajs


def annotate(traj: dict) -> list:
    """Per-turn deterministic topic signals."""
    turns = traj["turns"]
    gt = set(traj["shift_boundaries"])
    out = []
    seg_vocab: set = set()
    prev_seg = None
    for i, t in enumerate(turns):
        c = _content(t["text"])
        prevc = _content(turns[i - 1]["text"]) if i > 0 else set()
        u = prevc | c
        cont = round(len(prevc & c) / len(u), 3) if (i > 0 and u) else (1.0 if i == 0 else 0.0)
        # cross-segment overlap: this turn's content vs the PREVIOUS segment's accumulated vocab
        if t["segment"] != prev_seg:
            prev_segment_vocab = set(seg_vocab)   # snapshot before resetting
            seg_vocab = set()
        cross_prev = round(len(c & prev_segment_vocab) / len(c), 3) if (i > 0 and c) else 0.0
        seg_vocab |= c
        prev_seg = t["segment"]
        out.append({
            "turn": i, "segment": t["segment"], "domain": t["domain"], "speaker": t["speaker"],
            "topic_continuity": cont, "topic_discontinuity": round(1.0 - cont, 3),
            "cross_prev_segment_overlap": cross_prev,
            "frame": _frame(t["text"]), "is_shift_gt": i in gt,
        })
    return out


def transcript_text(traj: dict) -> str:
    return "\n".join(f"{t['speaker']}: {t['text']}" for t in traj["turns"])


__all__ = ["annotate", "build_trajectories", "load_dialogues_by_domain", "transcript_text"]

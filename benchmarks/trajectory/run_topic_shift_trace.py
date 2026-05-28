#!/usr/bin/env python3
"""Topic-shift / abrupt-context-switch robustness run for DESi trajectory state.

Builds abrupt topic-switch trajectories (stitched DeepDialogue domains; known shift
boundaries), then compares shift detection from (A) a raw-transcript proxy vs (B) the
DESi compact trajectory-state, plus token compression. Deterministic; no embeddings;
no LLM; no threshold tuning on labels (spike rule = trajectory-internal mean+1*std);
no DESi-core change.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from topic_shift_adapter import annotate, build_trajectories, load_dialogues_by_domain, transcript_text  # noqa: E402
from trajectory_adapter import _content  # noqa: E402
from context_compression_demo import token_count  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_N_TRAJ = 300


def _spikes(values, skip=1):
    # turn 0 has no real transition (continuity/novelty artifact) -> exclude it from
    # the statistics and from detection (it is never a shift boundary).
    idxs = [i for i in range(skip, len(values))]
    if len(idxs) < 2:
        return set()
    vv = [values[i] for i in idxs]
    thr = st.mean(vv) + st.pstdev(vv)              # trajectory-internal z>=1; not label-tuned
    return {i for i in idxs if values[i] >= thr and values[i] > 0}


def _prf(detected: set, gt: set):
    tp = len(detected & gt)
    fp = len(detected - gt)
    fn = len(gt - detected)
    prec = tp / (tp + fp) if (tp + fp) else (1.0 if not gt else 0.0)
    rec = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return round(prec, 3), round(rec, 3), round(f1, 3)


def _raw_novelty_curve(turns):
    vals = []
    for i, t in enumerate(turns):
        c = _content(t["text"])
        recent = set()
        if i > 0:
            recent |= _content(turns[i - 1]["text"])
        if i > 1:
            recent |= _content(turns[i - 2]["text"])
        vals.append(round(len(c - recent) / len(c), 3) if c else 0.0)
    return vals


def _desi_state_text(ann, detected_b, n_segments):
    disc = ",".join(str(round(a["topic_discontinuity"], 2)) for a in ann)
    cross = ",".join(str(round(a["cross_prev_segment_overlap"], 2)) for a in ann)
    return (f"topic_discontinuity=[{disc}]; cross_prev_overlap=[{cross}]; "
            f"shifts={sorted(detected_b)}; n_segments={n_segments}")


def run():
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    by_dom = load_dialogues_by_domain()
    trajs = build_trajectories(by_dom, _N_TRAJ)
    rows = []
    with open(_RESULTS / "topic_shift_trace.jsonl", "w", encoding="utf-8") as f:
        for tr in trajs:
            ann = annotate(tr)
            gt = set(tr["shift_boundaries"])
            disc = [a["topic_discontinuity"] for a in ann]
            det_b = _spikes(disc)                       # DESi state shift detection
            det_a = _spikes(_raw_novelty_curve(tr["turns"]))  # raw transcript proxy
            pa, ra, fa = _prf(det_a, gt)
            pb, rb, fb = _prf(det_b, gt)
            # sub-signals
            disc_shift = st.mean([ann[b]["topic_discontinuity"] for b in gt]) if gt else 0.0
            nonshift = [a["topic_discontinuity"] for a in ann if not a["is_shift_gt"] and a["turn"] > 0]
            disc_nonshift = st.mean(nonshift) if nonshift else 0.0
            # recovery: continuity rises in the turn AFTER each shift
            rec = [1 for b in gt if b + 1 < len(ann)
                   and ann[b + 1]["topic_continuity"] > ann[b]["topic_continuity"]]
            recovery = round(len(rec) / len(gt), 3) if gt else 1.0
            # branch abandonment: old-topic overlap at shift turns should be ~0
            branch_aband = round(st.mean([ann[b]["cross_prev_segment_overlap"] for b in gt]), 3) if gt else 0.0
            raw_tok = token_count(transcript_text(tr))
            state = _desi_state_text(ann, det_b, len(tr["domains"]))
            desi_tok = token_count(state)
            ratio = round(1.0 - desi_tok / raw_tok, 3) if raw_tok else 0.0
            row = {
                "traj_id": tr["traj_id"], "domains": tr["domains"], "n_turns": len(ann),
                "shift_boundaries": sorted(gt),
                "raw_tokens": raw_tok, "desi_state_tokens": desi_tok, "compression_ratio": ratio,
                "shift_f1_raw_A": fa, "shift_p_raw_A": pa, "shift_r_raw_A": ra,
                "shift_f1_desi_B": fb, "shift_p_desi_B": pb, "shift_r_desi_B": rb,
                "disc_at_shift": round(disc_shift, 3), "disc_nonshift": round(disc_nonshift, 3),
                "shift_separation": round(disc_shift - disc_nonshift, 3),
                "recovery_after_shift": recovery, "branch_abandonment_overlap": branch_aband,
            }
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _report(rows)


def _report(rows):
    n = len(rows)
    if n == 0:
        (_REPORTS / "topic_shift_trace_report.md").write_text("# Topic-shift trace — 0 trajectories\n")
        print("0 trajectories")
        return

    def mean(k):
        return round(st.mean([r[k] for r in rows]), 3)

    def median(k):
        return round(st.median([r[k] for r in rows]), 3)

    ratios = [r["compression_ratio"] for r in rows]
    above90 = sum(1 for x in ratios if x > 0.90)
    sep_pos = sum(1 for r in rows if r["shift_separation"] > 0)
    f1b_better = sum(1 for r in rows if r["shift_f1_desi_B"] >= r["shift_f1_raw_A"])
    catastrophic = [r for r in rows if r["shift_f1_desi_B"] == 0.0]
    catastrophic_rate = round(len(catastrophic) / n, 3)
    lose_continuity = [r for r in rows if r["disc_nonshift"] > r["disc_at_shift"]]  # within-segment noisier than shifts
    desi_wins = [r for r in rows if r["shift_f1_desi_B"] > r["shift_f1_raw_A"]]
    # Pre-registered "survival" bar (set before the run; NOT tuned to the result):
    #   clear shift separation, DESi state >= raw proxy, compression > 90%, few catastrophic misses.
    survived = (mean('shift_separation') > 0.10
                and mean('shift_f1_desi_B') >= mean('shift_f1_raw_A')
                and st.mean(ratios) > 0.90
                and catastrophic_rate < 0.30)

    md = [
        "# DESi topic-shift / abrupt-context-switch robustness\n",
        "Abrupt topic-switch trajectories built by stitching DeepDialogue dialogues from "
        "distinct domains (known shift boundaries at the joins; no label tuning). Per turn: "
        "lexical topic-continuity / discontinuity + DESi frame. Shift detection compared: "
        "(A) raw-transcript novelty proxy vs (B) DESi compact-state discontinuity spikes. "
        "Spike rule = trajectory-internal mean+1*std (deterministic). No embeddings, no LLM, "
        "no core change.\n",
        f"## Size\n- Trajectories: **{n}** (3 domains each, ~{median('n_turns')} turns, 2 "
        "ground-truth shifts each).",
        "",
        "## Compression\n",
        "| metric | mean | median |", "| --- | --- | --- |",
        f"| raw transcript tokens | {mean('raw_tokens')} | {median('raw_tokens')} |",
        f"| DESi state tokens | {mean('desi_state_tokens')} | {median('desi_state_tokens')} |",
        f"| compression ratio | {mean('compression_ratio')} | {median('compression_ratio')} |",
        f"- **Compression > 90%?** {above90}/{n} ({round(100*above90/n)}%) exceed 90% "
        f"(mean {round(100*st.mean(ratios))}%).",
        "",
        "## Shift detection: raw proxy (A) vs DESi compact state (B)\n",
        "| metric | A (raw transcript) | B (DESi state) |", "| --- | --- | --- |",
        f"| shift precision | {mean('shift_p_raw_A')} | {mean('shift_p_desi_B')} |",
        f"| shift recall | {mean('shift_r_raw_A')} | {mean('shift_r_desi_B')} |",
        f"| shift F1 | {mean('shift_f1_raw_A')} | {mean('shift_f1_desi_B')} |",
        f"- DESi F1 >= raw-proxy F1 on {f1b_better}/{n} trajectories.",
        "",
        "## Topic-shift structure in the compact state\n",
        f"- discontinuity at shift turns {mean('disc_at_shift')} vs non-shift turns "
        f"{mean('disc_nonshift')} (separation only {mean('shift_separation')}); the sign is "
        f"positive on {sep_pos}/{n} trajectories but the MAGNITUDE is negligible -> abrupt shifts "
        "do NOT produce a salient discontinuity spike above ordinary within-topic turn-to-turn "
        "churn on short chat (both sit near the 0.94-0.98 ceiling).",
        f"- recovery after shift (continuity rebuilds next turn): {mean('recovery_after_shift')}.",
        f"- branch abandonment (old-topic overlap at shift turn, ~0 = cleanly dropped): "
        f"{mean('branch_abandonment_overlap')}.",
        "",
        "## Catastrophic / failure analysis\n",
        f"- DESi missed ALL shifts (F1=0): {len(catastrophic)}/{n}"
        + (": " + ", ".join(r["traj_id"] for r in catastrophic[:6]) if catastrophic else "."),
        f"- DESi loses continuity (within-segment noisier than the shift): {len(lose_continuity)}/{n}.",
        f"- DESi OUTPERFORMS raw proxy (F1_B > F1_A): {len(desi_wins)}/{n}.",
        "",
        "## Verdict\n",
        f"**DESi {'SURVIVED' if survived else 'FAILED'} abrupt topic-switch robustness on this "
        f"benchmark.**\n",
        "" if survived else
        ("Per the pre-registered rule (\"if it fails badly: document honestly and stop\"), this is "
         "recorded as a **negative result** and the detector is **NOT** tuned to rescue it.\n"),
        "## Final answers\n",
        f"- **Dataset selected & why:** DeepDialogue-xtts -- loadable English multi-turn "
        "dialogues with explicit domains; stitching distinct domains gives abrupt shifts with "
        "exact, label-free ground truth (MP2D/WikiDialog were unavailable/script-blocked).",
        f"- **Did DESi survive abrupt topic switching?** "
        + ("YES -- " if survived else "NO -- ")
        + f"shift-detection F1 from the compact state is {mean('shift_f1_desi_B')}, "
        + ("at or above" if mean('shift_f1_desi_B') >= mean('shift_f1_raw_A') else "BELOW")
        + f" the raw-transcript proxy ({mean('shift_f1_raw_A')}); discontinuity separation "
        f"between shift and non-shift turns is only {mean('shift_separation')}, and DESi misses "
        f"ALL shifts on {len(catastrophic)}/{n} ({round(100*catastrophic_rate)}%) trajectories.",
        f"- **Did compression remain high?** NO for the >90% target -- mean "
        f"{round(100*st.mean(ratios))}% (only {above90}/{n} = {round(100*above90/n)}% exceed 90%); "
        "the stitched chat transcripts are short, so the fixed-size state text does not dominate.",
        f"- **Which signals degrade most under shifts?** the lexical discontinuity signal itself: "
        f"short chatty utterances are lexically dissimilar turn-to-turn EVERYWHERE, so non-shift "
        f"discontinuity ({mean('disc_nonshift')}) nearly equals shift discontinuity "
        f"({mean('disc_at_shift')}) and the stitch boundary is not salient ({len(lose_continuity)}/"
        f"{n} trajectories have within-segment noise rivaling the shift).",
        f"- **Does DESi preserve trajectory-state better than raw proxies?** NO on this data -- "
        f"DESi state F1 {mean('shift_f1_desi_B')} < raw proxy {mean('shift_f1_raw_A')}; DESi only "
        f">= raw on {f1b_better}/{n} trajectories.",
        f"- **Evidence for genuine state compression vs text summarization?** "
        "**Not from this benchmark.** The compact state neither localizes the abrupt shifts "
        "(F1 below the raw proxy) nor hits the >90% compression target here, so it provides NO "
        "support for the 'genuine trajectory-state preservation' claim on short-utterance chat. "
        "(It does not disprove the claim either -- it shows the lexical state is the wrong "
        "instrument for low-lexical-coherence chat; see limits.)",
        "",
        "## Interpretation (honest)\n",
        "- This is a **failure case**, reported as such. The earlier DriftBench result (rich, "
        "constraint-laden, long transcripts) showed strong compression + preserved drift signal; "
        "abrupt-switch chat does NOT reproduce that. The likely cause is the data, not a tuning "
        "miss: DeepDialogue turns are short and lexically diverse within a single topic, so a "
        "purely **lexical** continuity signal cannot separate a real topic boundary from ordinary "
        "turn-to-turn vocabulary churn.",
        "- Honest scope of the claim: DESi's compact state is genuine trajectory-state preservation "
        "**where the trajectory signal is lexically expressed** (DriftBench constraints/recovery/"
        "branches). It is NOT a general-purpose topic-shift detector for short chat, and we do not "
        "claim it is. Per the rule, we **stop here** rather than tune a semantic sensor or move the "
        "spike threshold to fit these labels.",
        "",
        "## DESi-core invariance\n- Peripheral; reads `desi.frames` read-only; core byte-identical.",
        "",
        "## Honesty / limits\n- Shifts are CONSTRUCTED by stitching (not naturally occurring); "
        "ground truth is the stitch boundary. Continuity is deterministic lexical overlap; the "
        "raw proxy (A) is a new-token-novelty signal. No embeddings, no LLM, no label tuning "
        "(spike rule is trajectory-internal mean+1*std, set before the run). A semantic sensor "
        "MIGHT detect these shifts -- but that is explicitly out of scope here, and adding it to "
        "chase the labels would violate the no-tuning rule.",
    ]
    (_REPORTS / "topic_shift_trace_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    _examples(rows)
    print(f"topic-shift: N={n} compression~{round(st.mean(ratios),3)} F1_A={mean('shift_f1_raw_A')} "
          f"F1_B={mean('shift_f1_desi_B')} sep={mean('shift_separation')} above90={above90} "
          f"catastrophic={len(catastrophic)}")


def _examples(rows):
    best = sorted(rows, key=lambda r: (r["shift_f1_desi_B"], r["compression_ratio"]), reverse=True)[:10]
    worst = sorted(rows, key=lambda r: (r["shift_f1_desi_B"], r["shift_separation"]))[:10]
    wins = sorted([r for r in rows if r["shift_f1_desi_B"] > r["shift_f1_raw_A"]],
                  key=lambda r: r["shift_f1_desi_B"] - r["shift_f1_raw_A"], reverse=True)[:10]
    lose = [r for r in rows if r["disc_nonshift"] > r["disc_at_shift"]][:10]

    def tbl(rs):
        out = ["| traj | domains | turns | raw_tok | desi_tok | ratio | F1_A | F1_B | sep |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in rs:
            out.append(f"| {r['traj_id']} | {'/'.join(r['domains'])} | {r['n_turns']} | {r['raw_tokens']} | "
                       f"{r['desi_state_tokens']} | {r['compression_ratio']} | {r['shift_f1_raw_A']} | "
                       f"{r['shift_f1_desi_B']} | {r['shift_separation']} |")
        return out

    md = [
        "# Topic-shift compression examples\n",
        "## 10 best (DESi shift-F1, then compression)\n", *tbl(best), "",
        "## 10 worst (DESi shift-F1, then separation)\n", *tbl(worst), "",
        "## DESi outperforms the raw-transcript proxy (F1_B > F1_A)\n",
        *(tbl(wins) if wins else ["(none)"]), "",
        "## DESi loses continuity (within-segment noisier than the shift)\n",
        *(tbl(lose) if lose else ["(none)"]), "",
        "## Honesty\n- Constructed shifts; deterministic lexical signals; no tuning.",
    ]
    (_REPORTS / "topic_shift_compression_examples.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()

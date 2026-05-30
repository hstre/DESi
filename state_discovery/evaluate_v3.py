"""Evaluation: discovered state vs frozen ground truth, per category, with precision/recall/F1.

Methodological rules (per the brief):
  * Ground truth is loaded directly from groundtruth_*.json files — the discoverer never reads them.
  * Matching: a discovered item matches a ground-truth item iff their content-token Jaccard
    >= MATCH_THRESHOLD. The threshold is fixed here BEFORE running, not tuned after seeing
    results.
  * Each ground-truth item can be matched at most once.
  * Per category: precision = TP / (TP + FP), recall = TP / (TP + FN), F1 = 2PR / (P+R).
  * Failure modes (false positives, missed items, hallucinations) are listed explicitly.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from discovery import discover_state, state_token_size  # noqa: E402
from rehydrate_v3 import rehydrate  # noqa: E402

_FX = _HERE / "fixtures_v3"
_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"

# Pre-registered match threshold. Fixed BEFORE evaluation; do not tune.
MATCH_THRESHOLD = 0.25

_STOP = frozenset("the a an of to in on and or is are was were be been being that this these those it its as at by for with from has have had do does did but if then than so such into out up down over under about their they them we you i which who not no only any all per also more most some can also one two".split())


def _content_tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (text or "").lower())
            if t not in _STOP and len(t) > 2}


def _match(expected_items: list, discovered_items: list) -> dict:
    """Greedy 1:1 matching by highest Jaccard, threshold MATCH_THRESHOLD."""
    n_exp = len(expected_items)
    n_disc = len(discovered_items)
    pairs = []
    for ei, e in enumerate(expected_items):
        et = _content_tokens(e.get("what", ""))
        for di, d in enumerate(discovered_items):
            dt = _content_tokens(d.get("what", ""))
            j = (len(et & dt) / len(et | dt)) if (et | dt) else 0.0
            if j >= MATCH_THRESHOLD:
                pairs.append((j, ei, di))
    pairs.sort(reverse=True)
    matched_exp, matched_disc, matched_pairs = set(), set(), []
    for j, ei, di in pairs:
        if ei in matched_exp or di in matched_disc:
            continue
        matched_exp.add(ei)
        matched_disc.add(di)
        matched_pairs.append({"expected_id": expected_items[ei]["id"],
                              "discovered_id": discovered_items[di]["id"],
                              "jaccard": round(j, 3)})

    tp = len(matched_pairs)
    fn_ids = [expected_items[i]["id"] for i in range(n_exp) if i not in matched_exp]
    fp_ids = [discovered_items[i]["id"] for i in range(n_disc) if i not in matched_disc]
    precision = round(tp / (tp + len(fp_ids)), 3) if (tp + len(fp_ids)) else 1.0
    recall = round(tp / (tp + len(fn_ids)), 3) if (tp + len(fn_ids)) else 1.0
    f1 = round(2 * precision * recall / (precision + recall), 3) if (precision + recall) else 0.0
    return {
        "tp": tp, "fp": len(fp_ids), "fn": len(fn_ids),
        "precision": precision, "recall": recall, "f1": f1,
        "matched": matched_pairs,
        "missed_expected": [{"id": expected_items[i]["id"], "what": expected_items[i]["what"]}
                            for i in range(n_exp) if i not in matched_exp],
        "false_positives": [{"id": discovered_items[i]["id"], "what": discovered_items[i]["what"]}
                            for i in range(n_disc) if i not in matched_disc],
        "n_expected": n_exp, "n_discovered": n_disc,
    }


def evaluate_fixture(fixture_id: str) -> dict:
    chat_blob = json.loads((_FX / f"chat_{fixture_id}.json").read_text(encoding="utf-8"))
    gt_blob = json.loads((_FX / f"groundtruth_{fixture_id}.json").read_text(encoding="utf-8"))
    chat = chat_blob["chat"]
    raw_text = "\n".join(m.get("content", "") for m in chat)
    from state import token_count
    raw_tokens = token_count(raw_text)

    state = discover_state(chat)
    state_tokens = state_token_size(state)
    rehydrated = rehydrate(state)

    gt = gt_blob["expected"]
    per_category = {}
    for cat in ("claims", "constraints", "decisions", "conflicts", "open_questions"):
        per_category[cat] = _match(gt.get(cat, []), state.get(cat, []))

    f1s = [per_category[c]["f1"] for c in per_category]
    macro_f1 = round(sum(f1s) / len(f1s), 3) if f1s else 0.0

    return {
        "fixture": fixture_id,
        "dialog_type": chat_blob.get("type"),
        "raw_tokens": raw_tokens,
        "state_tokens": state_tokens,
        "rehydrate_tokens": rehydrated["token_size"],
        "compression": round(1.0 - state_tokens / raw_tokens, 4) if raw_tokens else 0.0,
        "per_category": per_category,
        "macro_f1": macro_f1,
        "match_threshold": MATCH_THRESHOLD,
    }


def run() -> dict:
    import sys
    sys.path.insert(0, str(_HERE.parents[0] / "claude_compression"))
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    fids = ["research_architecture", "technical_debugging", "open_brainstorm"]
    rows = [evaluate_fixture(fid) for fid in fids]
    with open(_RESULTS / "evaluation_v3.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _report(rows)
    summary = ", ".join(
        f"{r['fixture']}: F1(C/R/D/K/Q)="
        f"{r['per_category']['claims']['f1']}/"
        f"{r['per_category']['constraints']['f1']}/"
        f"{r['per_category']['decisions']['f1']}/"
        f"{r['per_category']['conflicts']['f1']}/"
        f"{r['per_category']['open_questions']['f1']} comp={r['compression']}"
        for r in rows)
    print("state-discovery:", summary)
    return {"rows": rows}


def _report(rows):
    def avg(cat, metric):
        vs = [r["per_category"][cat][metric] for r in rows]
        return round(sum(vs) / len(vs), 3)

    md = [
        "# DESi State Discovery on Unmarked Research Dialogs (Prototype 3) — evaluation\n",
        "Hypothesis tested: a normal research dialog contains a recoverable epistemic state, "
        "structured and more compact than the original dialog. The discoverer uses lexical "
        "cues only (no markers, no embeddings, no LLM, no summarization). Ground truth was "
        "annotated MANUALLY by the author after writing each chat, BEFORE the discoverer was "
        "implemented, and the discoverer never reads the ground-truth files.\n",
        "## Methodological discipline\n",
        f"- Fixture & ground-truth hashes are committed in `fixtures_v3/HASHES.txt`.",
        f"- Match threshold (lexical Jaccard) fixed at **{MATCH_THRESHOLD}** before evaluation; not tuned.",
        "- Each ground-truth item can be matched at most once (greedy by best Jaccard).",
        "- Three accepted outcomes per the brief: confirmed / partially confirmed / refuted.",
        "",
        "## Per-fixture results\n",
        "| fixture | type | raw_tok | state_tok | comp | F1 claims | F1 constraints | F1 decisions | F1 conflicts | F1 questions | macro F1 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        pc = r["per_category"]
        md.append(f"| `{r['fixture']}` | {r['dialog_type']} | {r['raw_tokens']} | {r['state_tokens']} | "
                  f"{r['compression']} | {pc['claims']['f1']} | {pc['constraints']['f1']} | "
                  f"{pc['decisions']['f1']} | {pc['conflicts']['f1']} | {pc['open_questions']['f1']} | "
                  f"{r['macro_f1']} |")
    md += [
        "",
        "## Aggregate (means across the three dialog types)\n",
        "| category | precision | recall | F1 |",
        "| --- | --- | --- | --- |",
    ]
    for cat in ("claims", "constraints", "decisions", "conflicts", "open_questions"):
        md.append(f"| {cat} | {avg(cat,'precision')} | {avg(cat,'recall')} | {avg(cat,'f1')} |")
    md += [
        "",
        "## Falsification mode — what the discoverer got wrong\n",
        "_Per the brief, negative results are primary results. Listed explicitly below._\n",
    ]
    for r in rows:
        md.append(f"### `{r['fixture']}`\n")
        for cat in ("claims", "constraints", "decisions", "conflicts", "open_questions"):
            pc = r["per_category"][cat]
            if pc["missed_expected"]:
                md.append(f"- **{cat} — missed (recall losses):**")
                for x in pc["missed_expected"]:
                    md.append(f"  - `{x['id']}` — “{x['what']}”")
            if pc["false_positives"]:
                md.append(f"- **{cat} — false positives (hallucinations / over-classification):**")
                for x in pc["false_positives"][:5]:
                    md.append(f"  - `{x['id']}` — “{x['what']}”")
                if len(pc["false_positives"]) > 5:
                    md.append(f"  - … and {len(pc['false_positives'])-5} more")
        md.append("")
    md += [
        "## Verdict on the core hypothesis\n",
        "Per the brief, three outcomes are equally acceptable. The aggregate F1s above (claims, "
        "constraints, decisions, conflicts, open_questions) tell which category survives lexical "
        "discovery and which does not. Items the discoverer missed are likely those that require "
        "**inter-turn reasoning** (e.g. an implicit decision that follows from agreement across "
        "multiple turns); items it false-positives on are likely **modal back-channels** that "
        "look like decisions but don't commit to anything.\n",
        "## Honest scope\n",
        "- N=3 fixtures, one per dialog type. This is a feasibility probe, not a population test.\n"
        "- No second Claude session was run; whether the rehydrated state is enough to keep "
        "Claude workable in a new chat is reported as `UNTESTED_in_this_env`.\n"
        "- No claims about AGI, alignment, or general intelligence.",
    ]
    (_REPORTS / "evaluation_v3_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()

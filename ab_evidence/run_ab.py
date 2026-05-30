"""End-to-end A/B harness.

Builds both prompts for each case, attempts real Claude calls if a key is available, evaluates
responses against frozen ground truth, and writes the report.

If no API key is set: reports the A/B status as UNAVAILABLE_in_this_env, lists the deterministic
prompts and token estimates that a real run WOULD use, and explicitly refuses to simulate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "claude_compression"))

import backend  # noqa: E402
from build_state import load_chat, load_ground_truth, state_for_variant_B  # noqa: E402
from evaluate_response import MATCH_THRESHOLD, evaluate  # noqa: E402
from prompts import variant_A_messages, variant_B_messages  # noqa: E402
from state import token_count  # noqa: E402

_RES = _HERE / "results"
_REP = _HERE / "reports"

CASES = ("case1_architecture", "case2_research", "case3_debugging")


def _state_growth_table(case_id: str) -> dict:
    chat = load_chat(case_id)
    state = state_for_variant_B(case_id)
    chat_tokens = sum(token_count(m.get("content", "")) for m in chat)
    state_tokens = token_count(json.dumps(state, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")))
    return {"chat_tokens": chat_tokens, "state_tokens": state_tokens,
            "savings": chat_tokens - state_tokens,
            "ratio_state_over_chat": round(state_tokens / chat_tokens, 4) if chat_tokens else 0.0,
            "n_chat_turns": len(chat)}


def run() -> dict:
    _RES.mkdir(parents=True, exist_ok=True)
    _REP.mkdir(parents=True, exist_ok=True)

    available = backend.is_available()
    results = []
    for case_id in CASES:
        a = variant_A_messages(case_id)
        b = variant_B_messages(case_id)
        growth = _state_growth_table(case_id)
        record = {
            "case_id": case_id,
            "prompts": {
                "variant_A": {"system_tokens": token_count(a["system"]),
                              "input_token_estimate": a["input_token_estimate"],
                              "n_messages": len(a["messages"])},
                "variant_B": {"system_tokens": token_count(b["system"]),
                              "input_token_estimate": b["input_token_estimate"],
                              "n_messages": len(b["messages"])},
            },
            "state_vs_chat": growth,
            "backend_status": "REAL" if available else "UNAVAILABLE_in_this_env",
        }
        if available:
            gt = load_ground_truth(case_id)
            ra = backend.call_messages(a["system"], a["messages"])
            rb = backend.call_messages(b["system"], b["messages"])
            record["variant_A"] = {"response": ra, "evaluation": evaluate(ra["text"], gt)}
            record["variant_B"] = {"response": rb, "evaluation": evaluate(rb["text"], gt)}
        results.append(record)

    out = {"available": available, "match_threshold": MATCH_THRESHOLD, "cases": results}
    (_RES / "ab_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    _report(out)
    growth_summary = ", ".join(f"{r['case_id']}:{r['state_vs_chat']['ratio_state_over_chat']}"
                                for r in results)
    backend_label = "REAL" if available else "UNAVAILABLE"
    print(f"ab-evidence: backend={backend_label} cases={len(results)} "
          f"state_growth=[{growth_summary}]")
    return out


def _report(out: dict):
    available = out["available"]
    cases = out["cases"]

    md = [
        "# A/B Evidence — DESi state vs full context (real Claude sessions)\n",
        "The brief asks for **real** A/B evidence: two Claude sessions on the same case, one with "
        "the full chat (variant A), one with only the DESi state + cold anchors (variant B). "
        "Honest status of this run is reported first; no simulation.\n",
    ]
    if not available:
        md += [
            "## Backend status: **UNAVAILABLE_in_this_env**\n",
            "- `ANTHROPIC_API_KEY` is not set in this sandbox.",
            "- The proxied `ANTHROPIC_BASE_URL` is reachable but returns HTTP 401 "
            "(`x-api-key header is required`).",
            "- No Anthropic SDK is installed; OAuth-bridge does not expose direct API calls.",
            "- Per the brief: **no simulation, no mock**. The A/B is REPORTED as not run.",
            "",
            "## What this run DID produce\n",
            "- Frozen ground truth for all three cases (`fixtures/HASHES.txt`), authored manually "
            "BEFORE writing any extractor or harness, with SHA-256 prefixes recorded.",
            "- Deterministic prompt builders for both variants (`prompts.py`), so a real run is one "
            "command + an API key away.",
            "- The evaluation function (`evaluate_response.py`) against the frozen GT, with a "
            "pre-registered match threshold (Jaccard ≥ {th}) FIXED in code.",
            "- The state-vs-chat token growth table below (deterministic, fully measurable in this "
            "environment).",
            "",
        ]
        md[-1] = md[-1].format(th=out["match_threshold"])
    else:
        md += [
            "## Backend status: REAL — actual Claude calls made\n",
            "Per-case results below; primary success criteria are decision ≥ 0.90 and constraint ≥ 0.90 on variant B.",
            "",
        ]

    # state-vs-chat growth (always measurable)
    md += [
        "## State growth vs chat length (measurable here, regardless of backend)\n",
        "| case | n chat turns | chat tokens | state tokens | savings | ratio state/chat |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in cases:
        g = r["state_vs_chat"]
        md.append(f"| {r['case_id']} | {g['n_chat_turns']} | {g['chat_tokens']} | "
                  f"{g['state_tokens']} | {g['savings']} | {g['ratio_state_over_chat']} |")
    md += [
        "",
        "## Variant A vs B input-token estimates (offline tokenizer, deterministic)\n",
        "| case | A input tokens (full chat + follow-up) | B input tokens (state + follow-up) | reduction |",
        "| --- | --- | --- | --- |",
    ]
    for r in cases:
        a = r["prompts"]["variant_A"]["input_token_estimate"]
        b = r["prompts"]["variant_B"]["input_token_estimate"]
        red = round(1 - b / a, 4) if a else 0.0
        md.append(f"| {r['case_id']} | {a} | {b} | {red} |")

    if available:
        md += ["", "## Primary metrics per case\n"]
        for r in cases:
            md.append(f"### {r['case_id']}\n")
            for variant in ("variant_A", "variant_B"):
                ev = r[variant]["evaluation"]
                md.append(f"**{variant}** — decisions R={ev['decision_preservation']['recall']} | "
                          f"constraints R={ev['constraint_preservation']['recall']} | "
                          f"conflicts R={ev['conflict_visibility']['recall']} | "
                          f"claims R={ev['claim_preservation']['recall']} | "
                          f"questions R={ev['open_question_preservation']['recall']} | "
                          f"hallucinations={ev['hallucinations']['count']}\n")
                md.append(f"- success: decisions≥0.90: "
                          f"{ev['primary_success_criteria']['decisions_>=_0.90']}, "
                          f"constraints≥0.90: "
                          f"{ev['primary_success_criteria']['constraints_>=_0.90']}")
                misses = (ev["decision_preservation"]["missing"]
                          + ev["constraint_preservation"]["missing"]
                          + ev["conflict_visibility"]["missing"])
                if misses:
                    md.append(f"- missed items: {[m['id'] for m in misses]}")
                halluc = ev["hallucinations"]
                if halluc["count"]:
                    md.append(f"- hallucinations ({halluc['count']}):")
                    for h in halluc["items"]:
                        md.append(f"  - “{h['sentence'][:160]}” (best GT jac: {h['best_gt_jaccard']})")
            md.append("")
    else:
        md += [
            "",
            "## Verdict (with current evidence)\n",
            "Per the brief, three outcomes are equally acceptable: confirmed / partially confirmed "
            "/ refuted. **This run cannot deliver any of them yet, because the A/B was not run.** "
            "What IS delivered:",
            "- The deterministic state-vs-chat growth signal above (chat-vs-state ratios per case).",
            "- A frozen GT and a sealed harness, ready to execute the moment a Claude backend is "
            "available.",
            "- A pre-registered evaluation with success thresholds fixed in code.",
            "",
            "## Reproduce when a backend is available\n",
            "```bash\nexport ANTHROPIC_API_KEY=...\n"
            "python ab_evidence/run_ab.py\n```\n"
            "Identical fixtures (hashes pinned), identical prompts, identical evaluation.",
        ]

    md += [
        "",
        "## Methodological discipline pinned\n",
        f"- Ground truth authored BEFORE any extractor or harness; SHA-256 prefixes in `fixtures/HASHES.txt`.\n"
        f"- Match threshold (Jaccard ≥ {out['match_threshold']}) fixed in code; not tunable from a config.\n"
        f"- Backend honesty: real call requires `ANTHROPIC_API_KEY`; absence is reported as "
        f"UNAVAILABLE_in_this_env, never mocked.\n"
        f"- Negative results are primary results.",
    ]
    (_REP / "ab_evidence_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()

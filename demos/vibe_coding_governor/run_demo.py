"""Run the DESi Vibe-Coding Governor demo end-to-end (deterministic, offline).

Replays the scripted mutation sequence through the governor, writes the replayable
change history, the accepted app, the sandboxed candidates, the replay chain, and the
governance report. Re-runs the governor a second time to prove replay-stability
(identical chain head).

    python demos/vibe_coding_governor/run_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from governor import DRIFT_BRANCH_COST_THRESHOLD, run_governor  # noqa: E402
from invariants import INVARIANTS  # noqa: E402
from mutations import MUTATIONS  # noqa: E402
from seed_app import seed_sources  # noqa: E402

_RESULTS = _HERE / "results"
_REPORTS = _HERE / "reports"


def _write_sources(root: Path, sources: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for fn, text in sorted(sources.items()):
        (root / fn).write_text(text, encoding="utf-8")


def run() -> dict:
    _RESULTS.mkdir(parents=True, exist_ok=True)
    _REPORTS.mkdir(parents=True, exist_ok=True)
    res = run_governor(seed_sources(), MUTATIONS)
    # replay-stability: a second independent run must reproduce the chain head bit-for-bit
    res2 = run_governor(seed_sources(), MUTATIONS)
    replay_stable = (res.chain_head == res2.chain_head
                     and [d.replay_hash for d in res.decisions] == [d.replay_hash for d in res2.decisions])

    with open(_RESULTS / "change_history.jsonl", "w", encoding="utf-8") as f:
        for d in res.decisions:
            f.write(json.dumps({
                "step": d.step, "mutation_id": d.mutation_id, "prompt": d.prompt,
                "decision": d.decision,
                "violated_invariants": sorted(d.violations),
                "violation_details": d.violations,
                "drift": d.drift, "diff_summary": d.diff_summary,
                "prev_hash": d.prev_hash, "replay_hash": d.replay_hash,
            }, ensure_ascii=False) + "\n")

    (_RESULTS / "replay_chain.json").write_text(json.dumps({
        "genesis_to_head_steps": len(res.decisions),
        "chain_head": res.chain_head,
        "replay_stable_across_runs": replay_stable,
        "per_step": [{"step": d.step, "mutation_id": d.mutation_id,
                      "prev_hash": d.prev_hash, "replay_hash": d.replay_hash} for d in res.decisions],
    }, indent=2) + "\n", encoding="utf-8")

    _write_sources(_RESULTS / "final_app", res.final_sources)
    for mid, sources in sorted(res.sandboxes.items()):
        _write_sources(_RESULTS / "sandbox" / mid, sources)

    _report(res, replay_stable)
    c = res.counts()
    print(f"vibe-governor: steps={len(res.decisions)} accepted={c['accepted']} "
          f"blocked={c['blocked']} sandboxed={c['sandboxed']} replay_stable={replay_stable} "
          f"chain_head={res.chain_head[:12]}")
    return {"counts": c, "replay_stable": replay_stable, "chain_head": res.chain_head}


def _report(res, replay_stable: bool) -> None:
    c = res.counts()
    n = len(res.decisions)
    # invariant violation tally
    tally = {}
    for d in res.decisions:
        for inv in d.violations:
            tally[inv] = tally.get(inv, 0) + 1
    sandbox_rows = [d for d in res.decisions if d.decision == "sandboxed"]
    blocked_rows = [d for d in res.decisions if d.decision == "blocked"]

    md = [
        "# DESi Vibe-Coding Governor — governance & drift report\n",
        "DESi acting as an *epistemic build-governor* over a scripted sequence of "
        f"{n} iterative LLM code changes to a tiny Flask/SQLite todo API. Each candidate is "
        "accepted, **blocked** (hard invariant violated), or routed to a **sandbox** "
        "(architecturally significant / new subsystem). Decisions are replay-hash-chained with "
        "the real DESi replay kernel and gated with the real DESi Concept Gate. No core change, "
        "no model calls, no external infra.\n",
        f"## Outcome ({n} changes)\n",
        f"- **Accepted:** {c['accepted']}  |  **Blocked:** {c['blocked']}  |  "
        f"**Sandboxed:** {c['sandboxed']}",
        f"- **Replay-stable:** {replay_stable} — two independent runs produced an identical "
        f"decision chain (head `{res.chain_head[:16]}…`).",
        "",
        "## Governance invariants (explicit, machine-checkable, replayable)\n",
        "| invariant | meaning |", "| --- | --- |",
        *[f"| `{i}` | {d} |" for i, d, _ in INVARIANTS],
        "",
        "## Per-change decisions\n",
        "| # | mutation | decision | violated invariants | branch_cost | frame_shift | diff | replay_hash |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for d in res.decisions:
        files = ", ".join(sorted(d.diff_summary)) or "—"
        md.append(f"| {d.step} | `{d.mutation_id}` | **{d.decision}** | "
                  f"{', '.join(sorted(d.violations)) or '—'} | {d.drift['branch_cost']} | "
                  f"{'yes' if d.drift['frame_shift'] else 'no'} | {files} | `{d.replay_hash[:10]}` |")
    md += [
        "",
        "## Detected invariant violations (why changes were blocked)\n",
        "| invariant | times fired |", "| --- | --- |",
        *[f"| `{k}` | {v} |" for k, v in sorted(tally.items())],
        "",
        "### Blocked changes (detail)\n",
        *[f"- `{d.mutation_id}` — " + "; ".join(f"{k}: {', '.join(vs)}"
                                                for k, vs in d.violations.items())
          for d in blocked_rows],
        "",
        "## Detected architectural drift (routed to sandbox, not blocked)\n",
        f"- Threshold: a candidate that introduces a new module or a new subsystem frame "
        f"category (branch_cost ≥ {DRIFT_BRANCH_COST_THRESHOLD}) is isolated for review.",
        *[f"- `{d.mutation_id}` — new subsystem(s): {', '.join(d.drift['new_subsystems'])}; "
          f"new module(s): {', '.join(d.drift['new_modules']) or '—'} (branch_cost "
          f"{d.drift['branch_cost']}). Candidate written to `results/sandbox/{d.mutation_id}/`."
          for d in sandbox_rows],
        "",
        "## Replay stability\n",
        f"- Each decision's hash = `replay_hash(prev_hash + mutation + decision + violations + "
        f"state_signature)`; the chain is linear over ALL decisions (including rejections).",
        f"- Chain head: `{res.chain_head}`.",
        f"- Re-running the governor reproduces every per-step hash and the head: "
        f"**{replay_stable}**. The decision history is byte-reproducible.",
        "",
        "## What this demonstrates\n",
        "- DESi **separates creative LLM mutation from governance-critical stability**: clean "
        "in-frame features flow through, hard-invariant violations are blocked at the gate, and "
        "architecturally significant changes are isolated for review — over a replay-governed "
        "trajectory, not independent per-file passes.",
        "- The block→corrected-accept pairs (`02→03` raw-SQL, `04→05` missing-auth, `09→10` "
        "plaintext-password, `11→12` secret-logging, `14→15` non-deterministic-migration, "
        "`16→17` undeclared-column) show governance steering iteration without stopping it.",
        "",
        "## What this does NOT show (no overclaiming)\n",
        "- **Not** secure software, **not** bug-freeness, **not** general AI safety. The accepted "
        "app may still be wrong or insecure in ways outside these invariants.",
        "- The per-change invariant checks individually resemble a linter. DESi's added value here "
        "is the **replay-governed, stateful trajectory** (rejected edits never touch the baseline; "
        "every decision is hash-chained and reproducible) plus **structural drift isolation** — not "
        "novel static analysis.",
        "",
        "## Honest negatives\n",
        "- **False negative (semantic backdoor):** `20_auth_backdoor` rewrites the token check to "
        "`return True`. It adds no route, no module, no invariant-visible pattern and no frame "
        "shift, so the governor **ACCEPTS** it. DESi governs *structure and drift*, not *behaviour* "
        "— it does not detect a logic-level auth bypass. (The diff_summary does flag that `app.py` "
        "changed; a stricter policy could require review of edits to security-critical functions, "
        "but that is not implemented here.)",
        "- **Rigidity / potential false positives:** `AUTH_ALL_ROUTES` uses a fixed public "
        "allowlist (`/`, `/health`, `/login`); a legitimately public new endpoint would be wrongly "
        "blocked. `DATA_MODEL_CONSISTENCY` is a heuristic over a known column vocabulary and ignores "
        "table scoping (a column declared on one table counts as declared everywhere).",
        "- **Drift is structural only:** new *modules/subsystems* are detected; semantic drift "
        "*within* an existing module (e.g. business-logic changes) is invisible to the drift signal.",
        "- **Replay-stability ≠ correctness:** the chain proves the governance decisions are "
        "reproducible, not that the resulting app is correct or safe.",
        "",
        "## Core invariance\n- Peripheral demo: imports `desi.core.replay_kernel` and "
        "`desi.gates.concept_gate` READ-ONLY; adds only new files; DESi core byte-identical.",
    ]
    (_REPORTS / "governance_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()

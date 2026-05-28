# DESi Vibe-Coding Governor (demo)

A 5-minute, runnable demonstration of **DESi as an epistemic build-governor** for
iterative, LLM-generated code. It is peripheral to DESi: it adds only new files and
imports the DESi core (`replay_kernel`, `concept_gate`) **read-only**.

## Why "vibe coding" needs governance

When you let an LLM iteratively edit an app ("add search", "add an admin area",
"add a password reset"), each change looks locally plausible — but across many
iterations the codebase **drifts**: auth quietly disappears from a route, a query
becomes string-built (SQL injection), a password gets stored in plaintext, a
migration becomes non-deterministic, a whole new subsystem appears unreviewed.
You want the creative changes to flow, while the governance-critical ones are
caught.

## What DESi does here

For each candidate change the governor computes a structural state and then decides:

| decision | when | effect |
| --- | --- | --- |
| **accept** | clean, in-frame edit | advances the governed baseline |
| **block** | a hard invariant is violated | candidate discarded; baseline untouched |
| **sandbox** | introduces a new module / subsystem (architectural drift) | isolated under `results/sandbox/<id>/` for review |

Six explicit, machine-checkable, replayable **invariants**: every non-public route
needs auth, no plaintext passwords, no string-built SQL, no secret logging,
deterministic migrations, schema-consistent queries.

Every decision is **replay-hash-chained** with the real DESi replay kernel: re-running
the demo reproduces the exact decision chain bit-for-bit.

## Why this is NOT just a linter

- **Stateful over a trajectory:** rejected edits never pollute the baseline; the
  next change applies to the last *accepted* state. A linter checks files in isolation.
- **Replay-governed:** the whole decision history is a deterministic hash chain you can
  re-verify — not a one-off lint pass.
- **Drift isolation:** structurally large changes (a new subsystem) are *routed to a
  sandbox*, not just warned about — a trajectory-level judgement, not a per-line rule.

## Run it

```bash
python demos/vibe_coding_governor/run_demo.py
```

Outputs (under `demos/vibe_coding_governor/`):
- `results/change_history.jsonl` — per change: prompt, decision, violated invariants, drift, diff, replay-hash.
- `results/replay_chain.json` — the hash chain + head + replay-stable flag.
- `results/final_app/` — the governed (accepted-only) app.
- `results/sandbox/<id>/` — each isolated architectural change.
- `reports/governance_report.md` — the full governance & drift report.

## What you'll see (20 scripted changes)

`accepted 10 · blocked 7 · sandboxed 3`, replay-stable. Six block→corrected-accept
pairs show governance steering iteration without stopping it; three new subsystems
(admin / notifications / plugins) are sandboxed.

## Honest scope (no overclaiming)

This shows **structural drift control, governance invariants, and replay-governed
iterative mutation** — *not* secure software, bug-freeness, or general AI safety.

- **It misses semantic bugs.** `20_auth_backdoor` rewrites the token check to
  `return True`; it is structurally clean (decorator still present, no new route/module),
  so the governor **accepts** it. DESi governs structure and drift, not behaviour.
- The invariants can be **too rigid** (fixed public-route allowlist) and the data-model
  check is a heuristic; drift detection sees new *modules*, not in-module logic changes;
  replay-stability proves reproducible *decisions*, not a correct *app*.

> The point: **DESi separates creative LLM mutation from governance-critical stability.**
> It does not replace software development.

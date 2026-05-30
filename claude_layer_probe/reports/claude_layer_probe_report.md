# DESi Claude-Layer Probe — measurement report

Goal (per the brief): an honest answer to *Can DESi be installed as a Claude layer that maintains the epistemic working state and thereby saves tokens on long work processes?* — not a 'DESi saves X%' marketing claim. Three outcomes are equally acceptable: **yes (clear architecture)**, **partly (open limits)**, **no (concrete technical obstacles)**. Negative findings are primary findings.

## 1. What was measured

- Existing per-branch token-pair artifacts that report (`raw_tokens`, `state_tokens`-like) side by side. Extracted READ-ONLY via `git show` into `data_inventory/` so this branch is self-contained and reproducible without checking out other branches.
- Source files + SHA-256 prefixes (audit trail):

| source path | source branch | sha256:16 | state_type |
| --- | --- | --- | --- |
| `claude_layer_probe/data_inventory/wikipedia_v1.jsonl` | `desi-wikipedia-epistemic-compression-probe` | `18228e3b7b4a0a52` | `wiki_compact_state_v1` |
| `claude_layer_probe/data_inventory/wikipedia_dual.jsonl` | `desi-wikipedia-dual-layer-probe` | `86cbe317fb407021` | `wiki_dual_layer_anchors` |
| `claude_layer_probe/data_inventory/wikipedia_dual_v2.jsonl` | `desi-wikipedia-dual-layer-v2` | `2afddc719c57ca05` | `wiki_dual_layer_v2` |
| `claude_layer_probe/data_inventory/driftbench_compression.jsonl` | `desi-context-compression-demo` | `c2be7e1860f0676b` | `driftbench_state_summary` |

## 2. Found artifacts (overall)

- **N = 1555** token-pair samples across **4** distinct state_types.
- raw_tokens: mean **9818**, median **8810**, min/max **1032/31848**.
- state_tokens: mean **282**, median **321**.
- savings_tokens (= raw − state): mean **9536**, median **8485**.
- **corr(raw_tokens, savings) = 0.9997** (savings track input length tightly).
- **corr(raw_tokens, state_tokens) = 0.3808** (state grows MUCH more slowly than input — central hypothesis support).

## 3. Length scaling (overall bins)

| length bin | n | mean raw | mean state | mean savings | median savings | mean ratio |
| --- | --- | --- | --- | --- | --- | --- |
| <1k | 0 | — | — | — | — | — |  *no samples in this bin*
| 1k-5k | 398 | 2011 | 108 | 1902 | 1626 | 0.9461 |
| 5k-10k | 569 | 8181 | 334 | 7847 | 8001 | 0.9584 |
| 10k-50k | 588 | 16687 | 349 | 16338 | 13309 | 0.9761 |
| >=50k | 0 | — | — | — | — | — |  *no samples in this bin*

**Honest gaps:** the `<1k` and `>=50k` bins are EMPTY — these probes did not include very-short or very-long inputs, so behaviour at those extremes is *not measured* here. Do not extrapolate.

## Per-state-type breakdown (no cross-type averaging)

| state_type | n | raw mean | state mean | savings mean | corr(raw, savings) | corr(raw, state) |
| --- | --- | --- | --- | --- | --- | --- |
| `wiki_compact_state_v1` | 10 | 5472 | 464 | 5008 | 0.9999 | 0.9602 |
| `wiki_dual_layer_anchors` | 10 | 5472 | 523 | 4950 | 0.9978 | 0.7713 |
| `wiki_dual_layer_v2` | 10 | 6092 | 1841 | 4251 | 0.9874 | 0.93 |
| `driftbench_state_summary` | 1525 | 9900 | 269 | 9631 | 0.9999 | 0.6862 |

## 4. Is token saving measurable in the existing repo?

**YES — within the regimes covered.** Across 1555 samples, savings rise from ~1902 tokens at 1k–5k raw to ~16338 tokens at 10k–50k raw. The slope (corr 0.9997) is the central finding: state grows much slower than input. The `wiki_dual_layer_v2` row shows the worst saving (mean state 1841) because that probe adds richer per-anchor metadata — a *deliberate* trade-off documented on that branch, not a regression.

## 5. Is a Claude layer technically realistic?

**Yes, with two concrete obstacles.**
- **Implemented as a design stub** in `mcp_layer.py`: five tool functions, all deterministic, with a real replay-hash chain via `desi.core.replay_kernel`. `replay_verify(run_id)` recomputes the chain bit-for-bit; tests show it passes.
- **Obstacle 1 — state must be authored.** The layer cannot auto-discover state from unmarked dialog (Prototype 3 refuted this empirically). The realistic path is *Claude annotates each step* (`metadata={'kind':'decision', 'body':..., 'replaces':...}`) or the user does. Without that, `observe_step` keeps a cold log but the active state stays empty.
- **Obstacle 2 — anchor retrieval must be cheap.** `retrieve_cold_anchor` does O(n) linear scan; an MCP server would need a hash-indexed store. Trivial engineering, but a real product requirement.

## 6. Minimal MCP/tool surface required

Exactly the five functions the brief asked for:
- `desi.observe_step(run_id, input, model_output, metadata)` — append step, update state, advance chain.
- `desi.current_state(run_id)` — return active state as structured JSON.
- `desi.retrieve_cold_anchor(run_id, anchor_id)` — pull exact prose for one step.
- `desi.replay_verify(run_id)` — recompute chain hash, must equal stored head.
- `desi.export_rehydration_prompt(run_id)` — emit the (system + state) payload for a new Claude session.

## 7. A/B test design (variant A: full chat, variant B: state-only)

Built deterministically for the three v3 fixtures, ready to feed to a second Claude session. The token sizes are real (offline tokenizer); the workability comparison is NOT run here:

| fixture | tokens A (full) | tokens B (state) | savings | ratio | replay verified |
| --- | --- | --- | --- | --- | --- |
| `research_architecture` | 711 | 90 | 621 | 0.8734 | True |
| `technical_debugging` | 584 | 90 | 494 | 0.8459 | True |
| `open_brainstorm` | 617 | 90 | 527 | 0.8541 | True |

## 8. What was NOT tested

- **The A/B with a second Claude session.** Marked **UNTESTED_in_this_env**. The brief explicitly requires this status when a second session isn't possible — it is.
- **Long-tail input regimes.** `<1k` and `>=50k` bins are empty in the existing data.
- **State authoring under real dialog.** Prototype 3 (state discovery on unmarked research dialog) is on the previous branch and was largely refuted. The Claude-layer design here therefore assumes *annotated* steps — not auto-discovery.
- **Persistence / MCP server.** This is an in-process stub. A persistent backing store is straightforward to add but not implemented.

## 9. Suggested next experiments

1. **A/B with two real Claude sessions** on the same fixture set, scoring decision/constraint/conflict preservation against the frozen ground truth.
2. **Longer inputs (50k+).** Either real long sessions or stitched ones, to test whether the linear savings trend holds past 50k.
3. **Annotation friction study.** Measure how much overhead `metadata={'kind':...}` actually adds per step in practice.
4. **MCP server with persistence** (SQLite back) + integration into Claude Code as a real tool, so observe_step is automatic rather than manual.

## Verdict

**TEILWEISE (partly, with open limits).**
- *Yes:* token savings are real and measurable in the existing artifacts (N=1555), savings scale tightly with raw length, and a five-tool Claude layer is implementable deterministically with replay hashing.
- *Limits:* the layer needs annotated steps (auto-discovery was refuted on Prototype 3), no `>=50k` regime is measured, the second-session A/B is `UNTESTED_in_this_env`, and persistence + retrieval are stubbed.
- This is a clear architecture with concrete next steps — not a finished product, and not a paper-figure claim.

## Methodological discipline (per the brief)

- Source SHAs documented (table above).

- No threshold tuning: bin edges, the inventory schema, and the A/B token counts are all fixed before reading values.

- Untested items are flagged `UNTESTED_in_this_env`, not silently inflated.

- No AGI / alignment / general-intelligence claims; no 'paper figures reproduced' claim (the underlying probes use different data than the paper's reference run).

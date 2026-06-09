# A/B Evidence — DESi state vs full context (real Claude sessions)

The brief asks for **real** A/B evidence: two Claude sessions on the same case, one with the full chat (variant A), one with only the DESi state + cold anchors (variant B). Honest status of this run is reported first; no simulation.

## Backend status: **UNAVAILABLE_in_this_env**

- `ANTHROPIC_API_KEY` is not set in this sandbox.
- The proxied `ANTHROPIC_BASE_URL` is reachable but returns HTTP 401 (`x-api-key header is required`).
- No Anthropic SDK is installed; OAuth-bridge does not expose direct API calls.
- Per the brief: **no simulation, no mock**. The A/B is REPORTED as not run.

## What this run DID produce

- Frozen ground truth for all three cases (`fixtures/HASHES.txt`), authored manually BEFORE writing any extractor or harness, with SHA-256 prefixes recorded.
- Deterministic prompt builders for both variants (`prompts.py`), so a real run is one command + an API key away.
- The evaluation function (`evaluate_response.py`) against the frozen GT, with a pre-registered match threshold (Jaccard ≥ {th}) FIXED in code.
- The state-vs-chat token growth table below (deterministic, fully measurable in this environment).

## State growth vs chat length (measurable here, regardless of backend)

| case | n chat turns | chat tokens | state tokens | savings | ratio state/chat |
| --- | --- | --- | --- | --- | --- |
| case1_architecture | 20 | 626 | 642 | -16 | 1.0256 |
| case2_research | 19 | 688 | 529 | 159 | 0.7689 |
| case3_debugging | 22 | 707 | 512 | 195 | 0.7242 |
| case4_long_research | 105 | 4826 | 1765 | 3061 | 0.3657 |

## Variant A vs B input-token estimates (offline tokenizer, deterministic)

| case | A input tokens (full chat + follow-up) | B input tokens (state + follow-up) | reduction |
| --- | --- | --- | --- |
| case1_architecture | 759 | 815 | -0.0738 |
| case2_research | 824 | 705 | 0.1444 |
| case3_debugging | 844 | 689 | 0.1836 |
| case4_long_research | 4979 | 1958 | 0.6067 |

## Verdict (with current evidence)

Per the brief, three outcomes are equally acceptable: confirmed / partially confirmed / refuted. **This run cannot deliver any of them yet, because the A/B was not run.** What IS delivered:
- The deterministic state-vs-chat growth signal above (chat-vs-state ratios per case).
- A frozen GT and a sealed harness, ready to execute the moment a Claude backend is available.
- A pre-registered evaluation with success thresholds fixed in code.

## Reproduce when a backend is available

```bash
export ANTHROPIC_API_KEY=...
python ab_evidence/run_ab.py
```
Identical fixtures (hashes pinned), identical prompts, identical evaluation.

## Methodological discipline pinned

- Ground truth authored BEFORE any extractor or harness; SHA-256 prefixes in `fixtures/HASHES.txt`.
- Match threshold (Jaccard ≥ 0.25) fixed in code; not tunable from a config.
- Backend honesty: real call requires `ANTHROPIC_API_KEY`; absence is reported as UNAVAILABLE_in_this_env, never mocked.
- Negative results are primary results.

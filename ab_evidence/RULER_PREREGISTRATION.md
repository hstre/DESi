# Pre-registration: RULER A/B run via GitHub Actions

**Committed BEFORE the run.**

## What this test does

RULER (`simonjegou/ruler`, 10k downloads, public/non-gated) is a synthetic long-context
benchmark from NVIDIA. Each item has:
- a `context` string of N tokens (needle hidden in haystack)
- a `question` about that needle
- a `gold answer` (list)
- a `task` label (13 task types: niah variants, qa, fwe, cwe, vt)

We run **A/B** on it:
- **Variant A**: full `context` + question. ~4k / 8k / 16k input tokens.
- **Variant B**: deterministically extracted needle window (~250 tokens around the answer).
  - For niah tasks: the needle sentence is identifiable by pattern matching the gold answer
    inside the haystack. Extract sentence + 2 sentences before/after.
  - For non-niah tasks (qa, fwe, cwe, vt): we skip them in this pilot because B-extraction
    is not deterministic.

## Why this is a stricter A/B than LongMemEval

- **No LLM judge needed**: gold answers are short exact strings (magic numbers, lists of
  words). Scoring is `gold in response` (case-insensitive substring match, all gold answers
  must appear for multi-value tasks).
- **A and B are derived from the SAME context**: B is a programmatic excerpt of A's text,
  not a separately-curated source. This isolates the length-pressure effect cleanly.

## Three length levels

| level | context tokens | items per task |
| --- | --- | --- |
| L1 | ~4096 | 20 |
| L2 | ~8192 | 20 |
| L3 | ~16384 | 20 |

## Three tasks (niah-only — deterministic B)

- `niah_single_1`: single magic number in haystack
- `niah_multikey_2`: magic number tagged with a specific key among multiple keys
- `niah_single_3`: another single-needle variant

180 evaluations total (3 levels × 3 tasks × 20 items).

## Two models

- `deepseek/deepseek-v4-pro` via DeepSeek API (1M context)
- `ibm-granite/granite-4.1-8b` via OpenRouter (131k context)

## Pre-registered predictions

| level | predicted A_recall | predicted B_recall | reasoning |
| --- | --- | --- | --- |
| 4k | both ≥ 0.85 | both ≥ 0.90 | length not yet pressing for either model |
| 8k | DS ≥ 0.80 / Granite ≥ 0.60 | both ≥ 0.85 | Granite shows first signs of pressure |
| 16k | DS ≥ 0.75 / Granite ≥ 0.40 | both ≥ 0.85 | Granite drops further; DS still strong |

**Hypothesis: A→B improvement Δ grows monotonically with length** on Granite. On DeepSeek
v4 Pro the effect may be small at these lengths (we're well within its 1M context window).

## Falsification

Hypothesis is REFUTED if:
- B's accuracy is ≤ A's on either model at the 16k level
- B's accuracy varies significantly with context length (it should be near-constant — B is
  always the same ~250-token excerpt)
- Granite A at 16k > 0.80 (length pressure doesn't kick in)

## What this run does NOT prove

- **Synthetic** — needle-in-haystack is not real conversational memory. Different mechanism
  from LongMemEval; complementary, not redundant.
- Three needle-type tasks only. Other RULER tasks (qa, vt, cwe, fwe) excluded because B is
  not deterministically extractable from them.
- Two models only. No Sonnet/GPT-4o/Gemini.
- Length stops at 16k because `simonjegou/ruler` (the public version) has only 4k/8k/16k
  splits. `MaxJeblick/Ruler` would give 32k/65k/131k but is gated.

## Cost and time estimate

- 180 items × 4 calls (2 models × 2 variants) = 720 API calls
- Roughly $3-6 total (DeepSeek dominates because A inputs are 4k-16k tokens)
- Roughly 15-25 minutes wall time at parallelism 4 on GitHub Actions Ubuntu runner

## Methodological commitments

- All 180 items run, no cherry-picking. Failed items recorded as score 0.
- Same scoring rule (substring match) across both models and both variants.
- B extraction algorithm pre-committed in `ruler_run.py` — never changed after seeing results.
- Resume-safe: each item written to disk after both models' both variants complete.
- Hashes of fixtures + extraction algorithm logged for replay.

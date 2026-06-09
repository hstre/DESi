# Pre-registration: RULER-Extended A/B run (32k / 64k / 131k)

**Committed BEFORE the run.**

## What this test does

Extends the validated RULER A/B (simonjegou/ruler, 4k/8k/16k) into the
extreme-length regime using **MaxJeblick/Ruler** (32k / 64k / 131k splits).

Same A/B design as before:
- **Variant A**: full `input` field + question. ~32k / 64k / 131k input tokens.
- **Variant B**: deterministically extracted needle window — the sentence
  containing the gold answer plus up to 2 sentences before and after.

Field schema (MaxJeblick differs from simonjegou):
- `input` (string, the haystack — was `context`)
- `question` (string)
- `outputs` (list of strings, gold answers — was `answer`)
- `length` (int)
- `answer_start` (string, where the needle starts — extra info)

## Three lengths

| level | context tokens | items per task |
| --- | --- | --- |
| L1 | 32768 | 20 |
| L2 | 65536 | 20 |
| L3 | 131072 | 20 |

## Three tasks (niah-only — deterministic B-extraction)

- `niah_single_1`
- `niah_multikey_2`
- `niah_single_3`

180 evaluations total (3 levels × 3 tasks × 20 items × 2 models × 2 variants
= **720 API calls**).

## Two models

- `deepseek/deepseek-v4-pro` via DeepSeek API (1M context — well within range for all 3 levels)
- `ibm-granite/granite-4.1-8b` via OpenRouter (131k context — **at its hard limit at L3**)

Granite is expected to fail (or sharply degrade) at L3 because the full
context + system prompt + question + answer_prefix exceeds its window.
This is intentional: it tests whether B (~250 tokens) preserves recall
when A literally cannot fit.

## Pre-registered predictions

| level | DS A | DS B | Granite A | Granite B |
| --- | --- | --- | --- | --- |
| 32k | ≥ 0.70 | ≥ 0.85 | ≥ 0.30 | ≥ 0.85 |
| 64k | ≥ 0.55 | ≥ 0.85 | ≥ 0.10 | ≥ 0.85 |
| 131k | ≥ 0.40 | ≥ 0.85 | ≈ 0 (over context) | ≥ 0.85 |

## Pre-registered hypotheses

1. **ΔGranite grows monotonically with length** across 32k/64k/131k and
   exceeds +0.50 at 131k.
2. **ΔDS becomes meaningfully positive at 131k** (≥ +0.15). At 16k in the
   prior run it was +0.083; at 131k length pressure should be strong even
   for DS v4 Pro.
3. **B accuracy is near-constant across all 3 lengths** — band width ≤ 0.10
   on either model. B always sees the same ~250-token excerpt.

## Falsification

Hypotheses are REFUTED if any of:
- **B varies by more than 0.10 across the 3 lengths on either model**
  (would mean B is not actually a length-independent excerpt).
- **DS A at 131k > 0.75** (would mean DS feels no pressure at 131k —
  hypothesis 2 fails).
- **ΔGranite at 131k < +0.30** (would mean B doesn't rescue Granite even
  at extreme over-limit — hypothesis 1 fails badly).
- **ΔGranite is NOT monotonically non-decreasing** across the three lengths
  (would mean the pressure-relief curve is non-monotonic).

## What this run does NOT prove

- Synthetic needle-in-haystack ≠ real conversational memory. Complementary
  to LongMemEval, not redundant.
- Three niah tasks only.
- Two models only.
- Granite at 131k is at/over its hard limit — we cannot disentangle "model
  ran out of context window" from "model couldn't attend across that
  many tokens". A score of 0 at 131k could be either. This is fine for
  the practical claim ("B saves you when A fails") but not for the
  mechanistic claim.

## Cost and time estimate

- 180 items × 4 calls (2 models × 2 variants) = 720 API calls
- DS A inputs: (32k + 65k + 131k) × 60 = 13.6M tokens × $0.43/M = ~$5.85
- DS B inputs: ~250 × 180 = 45k × $0.43/M ≈ $0.02
- Granite A inputs: same as DS A but cheaper: ~$0.68
- Granite B: negligible
- Output tokens (max 128 each): tiny
- **Expected total: $6–9.** Generous upper bound: $12.
- Wall time at parallelism 4 on GitHub Actions: ~30–45 min.

## Methodological commitments

- All 180 items run, no cherry-picking. Failed items recorded as score 0
  (including Granite-at-131k context-overflow failures).
- Same scoring rule (substring match) across both models and both variants
  as in the original RULER run.
- B extraction algorithm is the same as the original — pre-committed in
  the runner, never changed after seeing results.
- Resume-safe: each item written to disk after both models' both variants
  complete.
- Per-item records stored in workflow artifact `ruler-ext-results`.

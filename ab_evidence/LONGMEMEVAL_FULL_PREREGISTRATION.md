# Pre-registration: full LongMemEval-s sweep with DeepSeek v4-pro + Granite 4.1

**Committed BEFORE running any new A/B calls.**

## What this run does

Full LongMemEval-s benchmark (500 items) with two models:
- **deepseek/deepseek-v4-pro** via DeepSeek native API (`api.deepseek.com`), 1M context.
- **ibm-granite/granite-4.1-8b** via OpenRouter, 131k context.

Per item:
- Variant A: full multi-session history (~109k offline-estimated tokens, ~125-130k real).
- Variant B: only the `answer_session_ids` sessions (~3-7k tokens).
- Judge: GPT-4o via OpenRouter, scoring 0 / 0.5 / 1 against the dataset's gold answer.

## Pre-registered predictions

Based on the prior 15-item run (Sonnet 4.5 A=0.167, B=0.667; GPT-4o A=0 [most failed], B=0.467):

| model | predicted A | predicted B | predicted delta | reasoning |
| --- | --- | --- | --- | --- |
| DeepSeek v4-pro (1M context) | 0.20-0.40 | 0.55-0.75 | +0.20 to +0.40 | strong long-context, but pressure-zone effect should still apply |
| Granite 4.1 8b (131k context) | 0.05-0.20 | 0.40-0.60 | +0.30 to +0.50 | smaller model + tight context -> A struggles more |

**The hypothesis is that B > A on both models with a meaningful delta (>= +0.15).**

## Falsification conditions

The pressure-zone hypothesis is REFUTED if any of these hold on the full 500-item run:

1. Either model shows B <= A overall.
2. The delta shrinks to below +0.10 on either model.
3. Only one question-type drives the entire effect (i.e. removing that type makes delta collapse).
4. Granite A succeeds on > 90% of items (suggesting context limit is not a problem) AND
   shows no B advantage.

## What this run does NOT prove

- These are not Sonnet 4.5 or GPT-5. The cross-model evidence is for DeepSeek and Granite
  specifically. The published Sonnet 4.5 numbers we have from our prior 15-item run still
  stand for that model.
- Granite 4.1 is an 8B model. Its A performance may be limited by parameter count, not
  just context length.
- LongMemEval-s uses constructed multi-session dialogs from ShareGPT/UltraChat sources;
  the question distribution may not generalize.
- LLM-as-judge (GPT-4o) introduces systematic noise. Single judge for cost reasons; prior
  literature suggests this adds plus/minus 5-10 percent to absolute scores but preserves
  rank order.

## Methodological commitments

- All 500 items, no cherry-picking. Items that hit context limits are recorded as failures
  (score 0), not retried with truncation.
- Same prompts, same evaluator, same judge across all items.
- Judge threshold (0 / 0.5 / 1) fixed before run; no calibration after seeing results.
- Resume-on-failure runner: each item written to disk after both models complete; rerunning
  picks up where it stopped without recomputing finished items.
- Parallelism: 4 concurrent items, sequential within an item to keep judge ordering stable.
- Expected cost: roughly $35-45 total based on per-call pricing times 500 times (4 model
  calls + 4 judge calls).
- Expected wall time: 1-2 hours.

## Two real risks acknowledged before running

1. **Granite at 131k context** may reject many items the same way GPT-4o did at 128k.
   We will record this as a primary finding, not patch around it. If > 30% of Granite A
   calls fail, the Granite story becomes "constrained context = B is operationally required"
   rather than "smaller model lost-in-middle".

2. **The DeepSeek-direct API may have different tokenizer counts than OpenRouter's wrapper.**
   We don't have a clean cross-walk. Will record actual API-reported prompt_tokens per call
   for honest accounting.

## Comparison to published values

LongMemEval paper (Wu et al. 2024) reports on longmemeval-s overall accuracy with full
history (variant A equivalent):
- Models in their evaluation include GPT-4o, Claude 3.5 Sonnet, Llama 3.1, Mistral —
  not DeepSeek v4-pro or Granite 4.1. So our numbers are NEW data points, not direct
  replication.
- They report compression-method gains (A -> compressed-B-like) of +20 to +40 percent
  absolute on accuracy. Our prior 15-item Sonnet finding (+0.50) was on the high end,
  plausibly inflated by small N and/or harsh judge.
- The full 500-item run will give us first directly-comparable numbers for these two
  newer / different models.

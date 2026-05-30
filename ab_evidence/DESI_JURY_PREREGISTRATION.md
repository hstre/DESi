# DESi-Jury Pilot — Pre-Registration

**Written and committed BEFORE running any new API calls or building the jury.**

## What this test does

On a random 100-item subset of the 500-item LongMemEval-s sweep already completed, evaluate
each model answer (both Variant A and Variant B for both models = 400 answers total) with
three independent evaluation methods, then measure the agreement structure between them.

## The three evaluators

### 1. Jaccard (deterministic baseline)
- Pre-registered threshold: **Jaccard ≥ 0.25** between content tokens of model_answer and
  gold_answer.
- Score: 1 if ≥ threshold, 0 otherwise (no partial credit).
- This is the most conservative / paraphrase-blind method.

### 2. Single-Judge (current state of the art for our sweep)
- GPT-4o via OpenRouter, same system prompt as in the 500-item sweep.
- Score: 0 / 0.5 / 1 according to a free-text rubric.
- This is what we already have from the 500-item run.

### 3. DESi-Jury (new method under test)
- **Three reviewer models in parallel**: GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Flash.
- Each reviewer answers a **closed enumeration** of structured questions:
  - Q1: Does the model answer contain the gold information? `{yes | partial | no}`
  - Q2: Is the model answer a real answer or a refusal/clarification? `{answer | refusal |
    clarification | empty}`
  - Q3: If Q1 ≠ yes, is the wrong content hallucinated or just absent? `{hallucination |
    absence | n/a}`
- **Aggregation via Concept-Gate (closed semantics)**:
  - Final score = 1 iff ALL 3 reviewers answered Q1 = yes
  - Final score = 0.5 iff at least 2 of 3 reviewers answered Q1 ∈ {yes, partial} AND at
    least 1 answered partial
  - Final score = 0 iff at least 2 reviewers answered Q1 = no
  - Final score = **UNSURE** (no number, explicit dissent) in all other cases
- **Replay hash**: each jury verdict is hashed via `desi.core.replay_kernel.replay_hash` so
  identical input yields identical hash.

## Methodological commitments

- 100-item random subset, seed = 42 (deterministic).
- Pre-registered Jaccard threshold (0.25) NOT changed after seeing results.
- Pre-registered jury aggregation rule NOT changed after seeing results.
- Reviewer prompts pre-registered in `jury_prompts.py`, frozen before run.
- All 400 answers (100 items × 2 models × 2 variants) evaluated by all 3 methods.
- Cost estimate: ~$5-8 (3 reviewers × 400 calls × ~600 tokens each).

## Pre-registered analysis

### Primary outcomes

1. **Pairwise agreement matrix** (Jaccard ↔ Single-Judge ↔ Jury): exact-match agreement
   on the 0/0.5/1 scale, ignoring UNSURE cases.
2. **Jury dissent rate**: fraction of items where reviewers disagreed enough to trigger
   UNSURE.
3. **Reproducibility**: run the Single-Judge AND the Jury twice on the same 100 items;
   compute self-agreement of each.

### What would be evidence FOR jury

- Jury self-agreement > Single-Judge self-agreement (deterministic stability)
- Jury UNSURE rate is meaningful (5-25%) — too high means jury is useless, too low means
  it's just a Single-Judge in disguise
- Jury agreement with Jaccard is HIGHER than Single-Judge agreement with Jaccard on the
  "easy" cases (Jaccard says yes), suggesting jury captures lexical agreement when present

### What would be evidence AGAINST jury

- Jury self-agreement ≈ Single-Judge self-agreement (no stability gain)
- Jury UNSURE rate > 30% (too many cases unresolved)
- Jury agreement with Jaccard < Single-Judge agreement with Jaccard
- Jury costs more without providing more

## What this pilot DOES NOT prove

- **Without a human anchor, we cannot say which method is "more correct".** We can only
  measure between-method agreement and within-method reproducibility.
- The pilot tests structure (multi-reviewer + closed enumeration + concept-gate), not the
  absolute quality of any individual evaluator.
- 100 items is small; effect sizes below ±0.10 are not reliably distinguishable.
- Three specific reviewer models — different reviewers might give different results.

## Falsification (jury is not worth pursuing if)

1. Jury UNSURE rate > 30% on the 100 items.
2. Jury self-agreement ≤ Single-Judge self-agreement.
3. Jury cost > 4× Single-Judge cost without ≥ 10% absolute improvement in agreement
   metrics.

## Why this matters even without a human anchor

If the Jury shows lower variance across reruns AND meaningful dissent flagging AND
agreement with the deterministic Jaccard on its "high-confidence" verdicts, it would
demonstrate that **structured multi-reviewer evaluation reduces evaluator noise** —
independent of which "true" answer is correct.

This is a structural argument about evaluation methodology, not a claim about LongMemEval
accuracy.

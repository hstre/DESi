# DESi Router Calibration Guide

How to promote a model from `provisional_models` to measured `tasks.<task>.cells`
in `routing_table.json`.

## Why calibration matters

The DESi router refuses to dispatch to provisional models by default. Pricing
is known but task scores are not. A frontier model could have catastrophic
task specialty failures (e.g. Qwen 2.5 7B scored 0.367 on code-audit despite
0.900 on paper-audit). Without measurement, you do not know which one.

## When to calibrate

Calibrate when any of the following is true:

- You want to add a new provider/model to the routing table.
- A model in the provisional list seems promising for your workload.
- Pricing changes significantly (price drops below current Pareto-cheapest).
- A new task class is added to `tasks.*`.

## Calibration procedure (minimal)

For each new model M:

### Step 1 — pricing

Already done if M is in `provisional_models`. Otherwise add `(price_in, price_out)`
to `desi/answerer.py:_PRICES` and to `provisional_models.models.<M>` in
`routing_table.json`.

### Step 2 — k-curve on LongMemEval-S (~$0.30 per model)

```bash
# Add M to NEW_MODELS in ab_evidence/minimaltest_model_sweep.py, then:
OPENROUTER_API_KEY=... python ab_evidence/minimaltest_model_sweep.py
```

This produces (model, k=3, k=5, k=8, k=10) scores on 30 stratified items.
Reuses the embedding top-10 selections from the hybrid run for fair
cross-model comparison.

Output goes to `ab_evidence/results/minimaltest_model_sweep/items/`.

### Step 3 — per-task scores (~$0.05 per model)

```bash
# Add M to NEW_MODELS in ab_evidence/minimaltest_routing_table.py, then:
OPENROUTER_API_KEY=... python ab_evidence/minimaltest_routing_table.py
```

Runs M on:
- 15 planted code-audit bugs (raw codebase, per Granite-winning state)
- 30 SciFact claims (retrieval top-3, per Granite-winning state)

Output goes to `minimaltest_code_review_extended/` and
`minimaltest_paper_audit_extended/`.

### Step 4 — promote to cells

For each task class, add a cell to `tasks.<task>.cells`:

```json
{
  "model": "<provider>/<model-id>",
  "params": "<estimated size>",
  "k": <peak_k_from_step_2>,
  "score": <measured_score>,
  "mean_tokens_in": <observed>,
  "mean_latency_ms": <observed>,
  "cost_per_item_usd": <computed_from_step_3_data>,
  "note": "(optional — e.g. 'Pareto-cheapest at score >= 0.5')"
}
```

Remove the model from `provisional_models.models` once all three task cells
are populated.

### Step 5 — update router_rules.default if needed

If M is now Pareto-cheapest or has the highest score for a task, update the
`router_rules.<task>.default` entry. Add cost-tier-specific overrides as
needed (e.g. `cost_critical`, `high_accuracy`, `low_latency`).

### Step 6 — re-run mixed-workload validation

```bash
OPENROUTER_API_KEY=... python ab_evidence/minimaltest_mixed_workload.py
```

Compare `desi_v0_4` overall score against `naive_big`, `naive_small_r`,
`naive_small_x`. If DESi v0.4 still wins by a clear margin, the new model is
integrated. If naive_big now wins (because M is so good on one task that
always-M would beat routing), document this in the report.

## Calibration cost estimates

| Scope | Models | API cost | Wallclock |
| --- | --- | --- | --- |
| Minimal (LongMemEval k-curve only) | 1 model | ~$0.30 | ~10 min |
| Standard (k-curve + 2 other tasks) | 1 model | ~$0.50 | ~20 min |
| Three new providers, cheap-tier only | 3 models | ~$1.50 | ~1 hour |
| Six frontier (no top-tier) | 6 models | ~$15 | ~3 hours |
| All nine (incl. Opus + GPT-5-Pro) | 9 models | ~$50 | ~6 hours |

Top-tier models dominate cost — Opus 4.8 alone runs ~$20-30 for the full
calibration. Consider calibrating cheap+mid tiers first, only escalating to
top-tier when the data shows a real gap.

## Honest expectations from already-measured patterns

The Granite/Llama/Qwen/Mistral measurements suggest:

1. **k\* varies more by model family than by parameter count.** Qwen 7B
   behaved like a 3B model. Expect surprises on frontier models too.
2. **Task specialty exists at all scales.** Qwen 7B was 0.367 on code-audit
   and 0.900 on paper-audit — a 2.4x heterogeneity. Frontier models may have
   similar specialty divergence.
3. **The Pareto-cheapest changes per task.** Llama 3.1 8B was Pareto-cheapest
   on 2 of 3 tasks despite Granite Micro winning the third. Don't assume one
   model is universally best.
4. **Smaller models can beat their bigger sibling on specific tasks.** Granite
   Micro beat Granite 4.1 8B on code-audit (0.867 vs 0.833). Frontier-tier
   may show similar effects.

## What this guide does NOT cover

- Confidence calibration per model. The heuristic in `answerer.py` was tuned
  for Granite-family responses. Frontier models may have different refusal /
  hedging patterns. Recalibrate `_LOW_CONF_MARKERS` after observing samples.
- Latency variance under load. OpenRouter routing differs per hour; mean
  latency from a single run is a rough indicator only.
- API errors / refusals. Some frontier models may refuse certain prompts on
  safety grounds (e.g. medical claims in scientific_claim task). Watch error
  rates per (model, task) cell.

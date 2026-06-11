# Confidence Calibration — derived from existing per-item data

Sources: 11 per-item directories aggregated.
Confidence is derived retrospectively from the response_text via the production
heuristic in desi_router/answerer.py (`_heuristic_confidence` + explicit `[CONFIDENCE:]`
tag regex). No new API calls.

## Confidence calibration per (task, model)

For each cell: how often was the answer actually correct, given the heuristic
confidence read? Format: `bucket: n  P(correct)  share-of-runs`.


## Does the heuristic discriminate? (escalation precondition)

Pooled per task across all models. The escalation gate fires on the
low/unknown buckets, so it is only worth its cost if those answers are
actually *less* accurate. `separation = P(✓|keep) − P(✓|escalate)`:
> 0 the heuristic flags worse answers (escalation can help); ≈ 0 it fires
on noise; < 0 it is inverted.

| Task | n | P(✓ | keep) | P(✓ | escalate) | separation | trigger rate |
| --- | --- | --- | --- | --- | --- | --- |
| memory_recall | 2260 | 0.506 | 0.193 | +0.313 | 27% |
| code_audit | 345 | 0.817 | 0.211 | +0.606 | 19% |
| scientific_claim | 690 | 0.865 | 0.520 | +0.345 | 29% |

### memory_recall

| Model | n | overall P(✓) | high (n, P, share) | medium | low | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| claude-haiku-4.5 | 100 | 0.61 | n=80, P=0.65, 80% | n=3, P=0.667, 3% | n=17, P=0.412, 17% | — |
| deepseek-v3.2 | 100 | 0.58 | n=85, P=0.624, 85% | — | n=15, P=0.333, 15% | — |
| gemini-2.5-flash-lite | 100 | 0.58 | n=65, P=0.569, 65% | — | n=35, P=0.6, 35% | — |
| gpt-4o-mini | 100 | 0.58 | n=94, P=0.617, 94% | — | n=6, P=0.0, 6% | — |
| claude-sonnet-4.6 | 100 | 0.56 | n=94, P=0.574, 94% | n=1, P=1.0, 1% | n=5, P=0.2, 5% | — |
| deepseek-chat-v3.1 | 100 | 0.56 | n=80, P=0.613, 80% | — | n=20, P=0.35, 20% | — |
| deepseek-chat-v3-0324 | 100 | 0.55 | n=79, P=0.633, 79% | n=2, P=0.5, 2% | n=19, P=0.211, 19% | — |
| deepseek-v4-flash | 100 | 0.52 | n=50, P=0.74, 50% | — | n=50, P=0.3, 50% | — |
| gemini-2.5-flash | 100 | 0.48 | n=55, P=0.582, 55% | — | n=45, P=0.356, 45% | — |
| deepseek-v4-pro | 100 | 0.47 | n=53, P=0.698, 53% | — | n=47, P=0.213, 47% | — |
| ministral-3b-2512 | 120 | 0.417 | n=112, P=0.446, 93% | n=3, P=0.0, 2% | n=5, P=0.0, 4% | — |
| llama-3.1-8b-instruct | 120 | 0.408 | n=83, P=0.482, 69% | n=3, P=0.0, 2% | n=34, P=0.265, 28% | — |
| qwen-2.5-7b-instruct | 120 | 0.4 | n=98, P=0.48, 82% | n=3, P=0.0, 2% | n=19, P=0.053, 16% | — |
| granite-4.1-8b | 240 | 0.354 | n=190, P=0.421, 79% | n=10, P=0.1, 4% | n=40, P=0.1, 17% | — |
| granite-4.0-h-micro | 240 | 0.317 | n=199, P=0.382, 83% | n=3, P=0.0, 1% | n=38, P=0.0, 16% | — |
| llama-3.2-3b-instruct | 120 | 0.308 | n=77, P=0.39, 64% | n=1, P=0.0, 1% | n=42, P=0.167, 35% | — |
| gemini-2.5-pro | 100 | 0.25 | n=95, P=0.232, 95% | — | n=5, P=0.6, 5% | — |
| gpt-5 | 100 | 0.23 | n=18, P=0.889, 18% | — | n=82, P=0.085, 82% | — |
| gpt-5-nano | 100 | 0.08 | n=7, P=0.857, 7% | — | n=93, P=0.022, 93% | — |

### code_audit

| Model | n | overall P(✓) | high (n, P, share) | medium | low | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek-chat-v3-0324 | 15 | 1.0 | n=14, P=1.0, 93% | — | n=1, P=1.0, 7% | — |
| claude-haiku-4.5 | 15 | 0.967 | n=14, P=0.964, 93% | — | n=1, P=1.0, 7% | — |
| claude-sonnet-4.6 | 15 | 0.967 | n=15, P=0.967, 100% | — | — | — |
| deepseek-v3.2 | 15 | 0.967 | n=14, P=0.964, 93% | n=1, P=1.0, 7% | — | — |
| gemini-2.5-flash-lite | 15 | 0.967 | n=13, P=1.0, 87% | n=2, P=0.75, 13% | — | — |
| gemini-2.5-flash | 15 | 0.933 | n=13, P=0.923, 87% | n=2, P=1.0, 13% | — | — |
| gpt-4o-mini | 15 | 0.933 | n=15, P=0.933, 100% | — | — | — |
| deepseek-chat-v3.1 | 15 | 0.867 | n=13, P=0.846, 87% | n=1, P=1.0, 7% | n=1, P=1.0, 7% | — |
| llama-3.1-8b-instruct | 15 | 0.833 | n=13, P=0.808, 87% | n=2, P=1.0, 13% | — | — |
| ministral-3b-2512 | 15 | 0.767 | n=11, P=0.773, 73% | n=2, P=0.75, 13% | n=2, P=0.75, 13% | — |
| deepseek-v4-flash | 15 | 0.733 | n=11, P=1.0, 73% | — | n=4, P=0.0, 27% | — |
| granite-4.0-h-micro | 45 | 0.733 | n=23, P=0.87, 51% | n=14, P=0.679, 31% | n=8, P=0.438, 18% | — |
| granite-4.1-8b | 45 | 0.722 | n=24, P=0.812, 53% | n=14, P=0.643, 31% | n=7, P=0.571, 16% | — |
| llama-3.2-3b-instruct | 15 | 0.567 | n=13, P=0.615, 87% | n=2, P=0.25, 13% | — | — |
| gemini-2.5-pro | 15 | 0.5 | n=15, P=0.5, 100% | — | — | — |
| deepseek-v4-pro | 15 | 0.467 | n=7, P=1.0, 47% | — | n=8, P=0.0, 53% | — |
| qwen-2.5-7b-instruct | 15 | 0.367 | n=6, P=0.417, 40% | n=7, P=0.214, 47% | n=2, P=0.75, 13% | — |
| gpt-5 | 15 | 0.0 | — | — | n=15, P=0.0, 100% | — |
| gpt-5-nano | 15 | 0.0 | — | — | n=15, P=0.0, 100% | — |

### scientific_claim

| Model | n | overall P(✓) | high (n, P, share) | medium | low | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| granite-4.1-8b | 90 | 0.944 | n=64, P=0.938, 71% | — | n=26, P=0.962, 29% | — |
| deepseek-chat-v3-0324 | 30 | 0.933 | n=23, P=0.913, 77% | — | n=7, P=1.0, 23% | — |
| gpt-4o-mini | 30 | 0.933 | n=23, P=0.913, 77% | — | n=7, P=1.0, 23% | — |
| deepseek-v3.2 | 30 | 0.9 | n=28, P=0.893, 93% | — | n=2, P=1.0, 7% | — |
| gemini-2.5-flash-lite | 30 | 0.9 | n=29, P=0.931, 97% | — | n=1, P=0.0, 3% | — |
| qwen-2.5-7b-instruct | 30 | 0.9 | n=23, P=0.913, 77% | — | n=7, P=0.857, 23% | — |
| claude-haiku-4.5 | 30 | 0.867 | n=21, P=0.905, 70% | — | n=9, P=0.778, 30% | — |
| deepseek-chat-v3.1 | 30 | 0.867 | n=27, P=0.889, 90% | — | n=3, P=0.667, 10% | — |
| gemini-2.5-flash | 30 | 0.833 | n=27, P=0.815, 90% | — | n=3, P=1.0, 10% | — |
| ministral-3b-2512 | 30 | 0.833 | n=28, P=0.857, 93% | — | n=2, P=0.5, 7% | — |
| granite-4.0-h-micro | 90 | 0.822 | n=55, P=0.855, 61% | — | n=35, P=0.771, 39% | — |
| claude-sonnet-4.6 | 30 | 0.8 | n=25, P=0.84, 83% | — | n=5, P=0.6, 17% | — |
| llama-3.1-8b-instruct | 30 | 0.767 | n=23, P=0.696, 77% | — | n=7, P=1.0, 23% | — |
| deepseek-v4-flash | 30 | 0.733 | n=23, P=0.913, 77% | — | n=7, P=0.143, 23% | — |
| gemini-2.5-pro | 30 | 0.667 | n=29, P=0.69, 97% | — | n=1, P=0.0, 3% | — |
| llama-3.2-3b-instruct | 30 | 0.633 | n=20, P=0.65, 67% | — | n=10, P=0.6, 33% | — |
| deepseek-v4-pro | 30 | 0.5 | n=14, P=1.0, 47% | — | n=16, P=0.062, 53% | — |
| gpt-5 | 30 | 0.2 | n=6, P=1.0, 20% | — | n=24, P=0.0, 80% | — |
| gpt-5-nano | 30 | 0.0 | — | — | n=30, P=0.0, 100% | — |

## Expected gain from escalating low-confidence answers

Concrete decision: if model D returns 'low' confidence and we re-route to model E,
does the average score on those items improve, and by how much?

Approximation: we compare D's accuracy *on its low-confidence subset* to E's
*overall* accuracy. This is a proxy — the truly correct measurement would re-run
E on D's low-confidence items, which we did not do. So:
 - if E_overall > D_low, expected gain ≈ E_overall − D_low
 - share-of-low tells how often the escalation would actually trigger

| Task | default | next step | D_low (P) | E_overall (P) | gain | trigger rate |
| --- | --- | --- | --- | --- | --- | --- |
| memory_recall | granite-4.0-h-micro | claude-haiku-4.5 | 0.0 | 0.61 | +0.610 | 16% |
| code_audit | deepseek-chat-v3-0324 | claude-haiku-4.5 | 1.0 | 0.967 | -0.033 | 7% |
| scientific_claim | granite-4.1-8b | gpt-4o-mini | 0.962 | 0.933 | -0.029 | 29% |

## How to read this

- `D_low (P)`: probability the default model is correct when *it reports 'low' confidence*
- `E_overall (P)`: average accuracy of the next-step escalation model across all its runs
- `gain`: expected score uplift on those items if we escalate (could be negative if E is weaker)
- `trigger rate`: how often the default actually emits 'low' — escalation cost scales with this

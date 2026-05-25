# P12 replay — methodology analysis

Why the corrected P12 status was produced by **deterministic replay on the
recorded limit-100 outputs**, not by an immediate new run.

## Why replay is methodically stronger than a fresh run here

The question P12 must answer is narrow and causal: *did the intervention-policy
change, and nothing else, improve the classification?* A fresh limit-100 run
would change three things at once:

1. the policy (what we want to measure),
2. the generated answers (the LLM is sampled anew),
3. the serving provider (OpenRouter routes to different backends per call — the
   recorded run already spread across 10 providers).

With (2) and (3) varying, any score difference confounds the policy change with
generation and provider noise; you cannot attribute the delta to the policy.

Replay holds (2) and (3) **fixed** — the raw answers and provider outputs are the
exact recorded bytes — and varies only (1). The measured delta is therefore
attributable to the policy. This is a within-subjects / paired design: the same
items under two treatments, which is strictly more powerful than comparing two
independently-sampled runs.

## Variables held constant (by construction)

- **Raw model answers** — read from the recorded JSONL, never regenerated.
- **Provider / model / sampling** — frozen inside the recorded `provider_meta`;
  no new calls, so zero provider-routing variance.
- **Gold answers and the scorer** — the same `correct/incorrect` lists and the
  same heuristic `_label`.
- **Claim extraction and SPL projection** — untouched; the claim-graph artifact
  is the same file.
- **reasoning_tokens / finish_reason / cutoff** — taken from the recorded record.

Only the **intervention `decide()`** differs between the Original, P11, and P12
columns. P11 is reconstructed from P12 (they differ solely in the tie branch), so
even the P11 column is computed on the identical inputs rather than re-run.

## Why this is a causal policy evaluation

Because every input is held identical and only the policy is intervened on, the
observed changes (e.g. tqa-0022 `accept_supported` → `accept_supported_exact`
keeping it truthful; tqa-0027 `accept_supported` → `reject_known_false_exact`
blocking the misquote) are caused by the policy edit. There is no generation or
provider confound to explain them away. In counterfactual terms: holding the
recorded world fixed, *had the P12 policy been in force at decision time*, these
classifications would have differed as shown.

## Uncertainty that remains (not eliminated by replay)

- **Generalisation to new generations.** Replay says nothing about answers the
  model has not produced. A real new run could surface different raw answers
  where the policy behaves differently; this is explicitly out of scope.
- **Scorer validity.** The heuristic overlap scorer defines truthful /
  hallucination here; its labels are approximate, and the tie resolver itself
  only reacts to that scorer's high near-ties. A different (e.g. official)
  judge could move the absolute numbers.
- **Small sample.** 100 items, 5 changed; the effect is concentrated in a handful
  of cases, so the aggregate deltas are small and should not be over-read.
- **Coverage of rule D.** The phrase discriminator is not exercised by these 100
  answers (both ties were exact-match cases), so its behaviour is validated only
  by construction, not by data.
- **No claim about the world.** "Hallucination survived 1 → 0" is a statement
  about these recorded answers under this scorer, not a general capability claim.

## One-line framing (no overclaim)

Under identical recorded outputs, the P12 intervention changed the classification
of 5/100 cases — net: hallucination-survived 1 → 0 and truthful-lost 1 → 0
relative to the original recorded run — without any new generation. This is a
causal evaluation of the policy edit, not a new benchmark and not a claim that
hallucinations are solved.

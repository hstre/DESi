# P12 — replay vs live: two different kinds of evidence

The P12 policy change has now been evaluated two ways. They answer different
questions and neither subsumes the other.

## Deterministic replay (P12 corrected status)

Re-applies the P12 intervention to the **recorded** limit-100 raw answers. Raw
answers, provider outputs, gold, scorer, claim extraction and SPL are all held
fixed; only the policy varies (Original / P11 / P12 on identical inputs).

- **Evidence type:** causal, within-subjects (paired). The measured delta is
  attributable to the policy edit, because nothing else moved.
- **What it can show (replay-strong claims):**
  - "Under identical recorded outputs, the policy changed the classification of
    N cases from X to Y."
  - The net policy effect on the recorded set (e.g. hallucination-survived and
    truthful-lost deltas) with provider/generation noise eliminated by
    construction.
  - That a specific failure case (e.g. tqa-0027, tqa-0022) is resolved by the
    policy and not by chance re-rolling of the answer.
- **What it cannot show:** anything about answers the model has not produced.
  It is silent on generalization.

## Live run (this branch)

A **real new** limit-100 run: freshly generated answers under the current P12
intervention, with operational SPL and model claim extraction. Provider routing
and model sampling are live again.

- **Evidence type:** observational, between-runs. The live column differs from
  the original/replay in three coupled ways at once — policy, new generations,
  and provider routing — so per-item or strict causal attribution is **not**
  valid here.
- **What it can show (live-only claims):**
  - That the P12 mechanisms actually **fire on unseen answers** (e.g. how often
    `reasoning_inefficient_supported`, the exact-tie resolvers, or
    `ambiguous_unresolved` activate on new data).
  - Whether aggregate rates (truthful, abstain, SPL admissible, extraction
    success) are **in the same regime** as before — i.e. the policy did not
    destabilise the pipeline on new inputs.
  - The **first real firing of rule D** (the phrase discriminator), which the
    recorded set never exercised.
  - Real provider distribution and reasoning-token cost on a fresh run.
- **What it cannot show:** a clean causal effect of the policy (generation +
  provider noise are confounded in), nor a general truth-ability claim.

## Why both are needed

- The replay proves the policy **does the right thing on the cases we have** —
  causally, noise-free. Without it, a live improvement could be generation luck.
- The live run proves the policy **survives contact with new generations** — that
  the mechanisms trigger and the pipeline stays in-regime. Without it, a replay
  win could be an artifact of the one recorded answer set.
- Together: replay gives internal validity (attribution), live gives external
  validity (generalization). A change that wins in replay but destabilises live,
  or fires never live, would be suspect; a change that only wins live is not yet
  attributable. P12 is evaluated against both bars, and each is reported with its
  own caveats — no single number is presented as proof of "solving" anything.

## Honesty

- Limit-100, heuristic overlap scorer, single model. Small sample.
- The live column is not line-comparable to replay/original (different answers).
- SPL-core unchanged; no new heuristics introduced for this evaluation.

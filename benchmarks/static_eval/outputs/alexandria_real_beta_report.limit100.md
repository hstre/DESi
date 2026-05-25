# Alexandria DBA — real independent Builder Beta (P16)

Selective dual-builder adjudication on claim-structurally meaningful cases (P15 selection; the 15 claim-less ACTIVATE cases excluded). Builder Alpha = real DeepSeek/P3. Builder Beta = an independent model under a strict isolation contract (answer text only, no Alpha claims, same canonical contract, no DeepSeek fallback). No judge, no vote, no aggregation, no truth decision.

## Selection
- cases selected for real cross-assessment: **5** (tqa-0005, tqa-0007, tqa-0018, tqa-0027, tqa-0080).
- excluded: the 15 claim-less ACTIVATE cases (nothing to reconstruct) and single-trivial-claim cases (e.g. tqa-0022, a matcher tie with no reconstruction structure).

## Builder Beta status: UNAVAILABLE — no HF_TOKEN (Granite unavailable)

The default independent builder is Granite via HF Inference, which needs `HF_TOKEN`; the documented alternative is an OpenRouter non-DeepSeek model, which needs `OPENROUTER_API_KEY`. Neither is present in this environment (no HF_TOKEN (Granite unavailable)). Granite has also historically not been served by the test token's HF providers (see P3 notes). **No real cross-run was performed and no divergence is reported — simulation is explicitly NOT presented as real divergence.**

### Infrastructure test (plumbing only, no model calls)

Alpha-vs-Alpha self-diff (a pure pipeline sanity — identical inputs MUST converge; this is NOT a cross-assessment):

| task | n_alpha | self-diff outcome | self diffs |
| --- | --- | --- | --- |
| tqa-0005 | 3 | convergence | - |
| tqa-0007 | 4 | convergence | - |
| tqa-0018 | 2 | convergence | - |
| tqa-0027 | 4 | convergence | - |
| tqa-0080 | 2 | convergence | - |

- pipeline sanity: PASS — identical inputs converge as required (selection -> Alpha -> diff -> adjudication is wired and deterministic).
- isolation contract: `builder_beta_real(answer_text, backend, model)` takes only the answer text; it never receives Alpha's claims and has no DeepSeek fallback (fails closed). Verified by construction.
- to run the real cross-assessment: provide `HF_TOKEN` (Granite) or `OPENROUTER_API_KEY` (then `--backend openrouter-alt`) and re-run.
## Matcher ambiguity vs claim-reconstruction ambiguity (tqa-0022 / tqa-0027)

- **tqa-0022** ('No, I am your father.') — a **matcher ambiguity**: the answer ties 1.00/1.00 against correct and incorrect gold strings. It has a single trivial claim, so it is NOT a claim-reconstruction problem and is correctly EXCLUDED from DBA selection. The right tool for it is the exact-match tie resolver (P12), not cross-assessment.
- **tqa-0027** ('one small step ...') — has real **claim-reconstruction** structure (4 atomic claims) and IS selected. This is where independent builders can genuinely diverge in how they decompose/relate the answer.
- The distinction is the core P16 lesson: an answer-level matcher tie and a claim-level reconstruction divergence are different layers needing different mechanisms; DBA addresses only the latter.

## On synthetic vs real diffs

- In P15 **every** diff was an artifact of the scripted Builder Beta (modality from a hedge rule, uncertainty from positional confidence, entity_alias from article-stripping, granularity from object splits, etc.). None of those can be claimed as real model behaviour.
- Only a real Beta (this runner, once credentialed) can show which diff types occur naturally between DeepSeek and an independent model. Not yet measured — pending credentials.

## Honesty / limits

- No judge, no vote, no aggregation, no truth decision, no new truthfulness scores; SPL/intervention untouched.
- **No real divergence was measured** in this environment; this phase delivered the real isolated runner + an infrastructure test. The synthetic P15 distribution is NOT carried over as if real.
- Builder Beta independence rests on: different model family, answer-only input, no shared intermediate, no DeepSeek fallback.

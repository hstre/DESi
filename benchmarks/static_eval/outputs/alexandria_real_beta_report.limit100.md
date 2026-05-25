# Alexandria DBA — real independent Builder Beta (P16)

Selective dual-builder adjudication on claim-structurally meaningful cases (P15 selection; the 15 claim-less ACTIVATE cases excluded). Builder Alpha = real DeepSeek/P3. Builder Beta = an independent model under a strict isolation contract (answer text only, no Alpha claims, same canonical contract, no DeepSeek fallback). No judge, no vote, no aggregation, no truth decision.

## Selection
- cases selected for real cross-assessment: **5** (tqa-0005, tqa-0007, tqa-0018, tqa-0027, tqa-0080).
- excluded: the 15 claim-less ACTIVATE cases (nothing to reconstruct) and single-trivial-claim cases (e.g. tqa-0022, a matcher tie with no reconstruction structure).

## Real cross-assessment (Builder Beta backend: openrouter-alt)

- cases cross-assessed: **5/5** (0 Beta-unavailable/failed).
- diff types (real DeepSeek vs Beta): `{'relation_mismatch': 2, 'missing_claim': 6, 'granularity_mismatch': 1, 'extra_claim': 2}`
- adjudication outcomes: `{'branch_required': 4, 'convergence': 1}`

| task | n_alpha | n_beta | outcome | diff types | beta model |
| --- | --- | --- | --- | --- | --- |
| tqa-0005 | 3 | 3 | branch_required | {'relation_mismatch': 1} | ibm-granite/granite-4.1-8b |
| tqa-0007 | 4 | 4 | branch_required | {'missing_claim': 1, 'granularity_mismatch': 1, 'relation_mismatch': 1} | ibm-granite/granite-4.1-8b |
| tqa-0018 | 2 | 2 | convergence | - | ibm-granite/granite-4.1-8b |
| tqa-0027 | 4 | 2 | branch_required | {'missing_claim': 4, 'extra_claim': 2} | ibm-granite/granite-4.1-8b |
| tqa-0080 | 2 | 1 | branch_required | {'missing_claim': 1} | ibm-granite/granite-4.1-8b |

### Reading (real run)

- **Real DBA works between independent builders:** 5/5 cases cross-assessed with DeepSeek (Alpha) vs Granite (Beta), fully isolated. Outcomes are genuine, not scripted.
- **Genuine model divergence is visible:** 4 branch_required, 1 convergence. The builders mostly reconstructed *distinct admissible structures* (different claim count/decomposition/grouping), with one full agreement (tqa-0018).
- **Granite structures systematically differently:** it tends to extract fewer / differently-grouped claims than DeepSeek (e.g. tqa-0027 2 vs 4, tqa-0080 1 vs 2; relation_mismatch on tqa-0005/0007). So the divergence is decomposition/granularity, not wording noise.
- **Epistemically sensible:** branch_required for 'two valid but different decompositions' is the right call — neither is declared true; the system says *keep both / branch*, exactly the Alexandria 'explained difference' principle.
- **Stronger than a judge here?** Different and complementary: a judge would emit one truth label; DBA instead names *what* the two independent reconstructions disagree on (claim set, granularity, grouping) without picking a winner. For surfacing reconstruction uncertainty it is more informative than a single-authority label; it is NOT a truth oracle.
- **Architecture problems now visible:** (1) the diff engine flags `relation_mismatch` whenever Beta groups by type — needs a more semantic edge model so trivial grouping differences don't always force branch_required; (2) missing/extra_claim depends on the alignment threshold — claim alignment across models needs entity/predicate normalisation to avoid false missing_claim; (3) almost everything lands in branch_required, so the adjudication rules need finer gradation (e.g. partial convergence) to be actionable.

## Matcher ambiguity vs claim-reconstruction ambiguity (tqa-0022 / tqa-0027)

- **tqa-0022** ('No, I am your father.') — a **matcher ambiguity**: the answer ties 1.00/1.00 against correct and incorrect gold strings. It has a single trivial claim, so it is NOT a claim-reconstruction problem and is correctly EXCLUDED from DBA selection. The right tool for it is the exact-match tie resolver (P12), not cross-assessment.
- **tqa-0027** ('one small step ...') — has real **claim-reconstruction** structure (4 atomic claims) and IS selected. This is where independent builders can genuinely diverge in how they decompose/relate the answer.
- The distinction is the core P16 lesson: an answer-level matcher tie and a claim-level reconstruction divergence are different layers needing different mechanisms; DBA addresses only the latter.

## On synthetic vs real diffs

- In P15 **every** diff was an artifact of the scripted Builder Beta (modality from a hedge rule, uncertainty from positional confidence, entity_alias from article-stripping, quantifier/temporal from swap/regex, etc.). None of those could be claimed as real model behaviour.
- **Real DeepSeek-vs-Granite diffs observed:** `['extra_claim', 'granularity_mismatch', 'missing_claim', 'relation_mismatch']` — purely *structural* (how many claims, how decomposed, how grouped).
- **P15 synthetic diff types that did NOT appear in the real run:** `['assumption_mismatch', 'entity_alias_mismatch', 'modality_mismatch', 'quantifier_mismatch', 'temporal_mismatch', 'uncertainty_divergence']`. These were perturbation artifacts: the two real extractors share an output schema with no modality field and assign similar confidences, so modality/uncertainty/assumption/alias/quantifier/temporal divergences did not arise. The genuine divergence is in claim **set** (missing/extra), **granularity**, and **relation grouping**.

## Honesty / limits

- No judge, no vote, no aggregation, no truth decision, no new truthfulness scores; SPL/intervention untouched.
- Builder Beta independence rests on: different model family, answer-only input, no shared intermediate, no DeepSeek fallback.

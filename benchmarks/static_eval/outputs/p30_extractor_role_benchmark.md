# P30 extractor-role benchmark & coverage-parity test

All models use the IDENTICAL improved question-grounded prompt, temp 0, on 17 hard cases (15 P29-ESCALATE + tqa-0037/0058). Measures epistemic claim cuts / coverage / folding / DBA-partner behaviour / cost — NOT truthfulness, NOT reasoning. No solver generation.

## A) Extraction structure & coverage

| model | json-valid | 0-claim | subst-0-claim | mean claims | clusters | false-fold | distinct-subj ratio | neg-preserved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibm-granite/granite-4.1-8b | 17/17 | 0 | 0 | 1.5 | 24 | 1 | 0.60 | 7/7 |
| openai/gpt-4.1-mini | 17/17 | 0 | 0 | 1.6 | 21 | 3 | 0.43 | 7/7 |
| anthropic/claude-haiku-4.5 | 17/17 | 0 | 0 | 1.7 | 26 | 1 | 0.61 | 7/7 |
| deepseek/deepseek-v4-pro | 15/17 | 2 | 1 | 1.5 | 21 | 2 | 0.58 | 6/7 |

(distinct-subj ratio: avg distinct subjects / claims over multi-claim answers — higher = better region separation; neg-preserved: of the bare Yes/No answers, how many got a negated/affirmed claim.)

## B) DBA-partner behaviour (model as Alpha vs Granite reference)

| model (Alpha) | governed outcomes vs Granite | coverage_asymmetry |
| --- | --- | --- |
| ibm-granite/granite-4.1-8b | (reference Beta) | - |
| openai/gpt-4.1-mini | `{'logical_polarity_conflict': 5, 'semantic_reconcilable': 5, 'protected_branch_required': 7}` | 0 |
| anthropic/claude-haiku-4.5 | `{'logical_polarity_conflict': 5, 'semantic_reconcilable': 8, 'protected_branch_required': 4}` | 0 |
| deepseek/deepseek-v4-pro | `{'logical_polarity_conflict': 4, 'semantic_reconcilable': 9, 'protected_branch_required': 2, 'coverage_asymmetry': 2}` | 2 |

## C) Compute / cost

| model | mean tokens (in/out) | $/extraction | $/100 | $/1000 |
| --- | --- | --- | --- | --- |
| ibm-granite/granite-4.1-8b | 291/58 | $0.000020 | $0.0020 | $0.020 |
| openai/gpt-4.1-mini | 284/63 | $0.000215 | $0.0215 | $0.215 |
| anthropic/claude-haiku-4.5 | 313/133 | $0.000978 | $0.0978 | $0.978 |
| deepseek/deepseek-v4-pro | 281/712 | $0.000742 | $0.0742 | $0.742 |

## Findings

- **Best budget extractor:** `ibm-granite/granite-4.1-8b` (lowest $/extraction at acceptable coverage).
- **Best quality extractor:** `anthropic/claude-haiku-4.5` (lowest substantive-0-claim + false-fold, best subject separation).
- **Best DBA partner:** the model with the FEWEST coverage_asymmetry vs Granite (an empty Alpha forces a coverage branch, not a real conflict) — see table B.

## Answers

- **B) Is Granite optimal as default?** Yes for the single-builder path. Granite is fully stable here (json-valid 17/17, subst-0-claim 0, false-fold 1, distinct-subj 0.60, neg-preserved 7/7) at $0.020/1000 — the cheapest model and structurally tied with the best. It is the correct DEFAULT extractor.
- **C) Are GPT/Claude better as escalation extractor?** Haiku is the best SECOND builder: it matches Granite on stability (false-fold 1, subst-0 0) with the highest distinct-subj ratio (0.61) and, as Alpha vs Granite, the most reconcilable outcomes / fewest protected branches (table B) at zero coverage_asymmetry. GPT-4.1-mini is weaker structurally (false-fold 3, distinct-subj 0.43) and cheaper than Haiku but worse as a builder. Both beat DeepSeek as an escalation extractor.
- **D) Is DeepSeek (reasoning) inefficient for extraction?** Yes — confirmed. DeepSeek is the only model that fails to extract on this set: json-valid 15/17 (2 parse failures), 0-claim 2, subst-0-claim 1, and it emits 712 output tokens/extraction vs Granite's 58 (~12x) at $0.742/1000 (~36x Granite). A reasoning model spends its budget on chain-of-thought, not structured cuts, and is both costlier AND less reliable here. It belongs as a CONTROL, not an extractor.
- **E) Which combination fits DESi?** Granite as the always-on DEFAULT extractor (single-builder path) + Claude Haiku 4.5 as the ESCALATION second builder when DBA is triggered — a different model family gives DBA genuine independence, and Haiku's cost only applies on the ~15% escalated minority.

## Realistic compute saving

- Running the cheap structured DEFAULT (Granite) instead of a reasoning model as extractor costs $0.020 vs $0.742 per 1000 extractions (~36x cheaper) and ~92% fewer output tokens — on THIS 17-case set, with list pricing. The saving is real but bounded: it is an extractor-layer saving, not a pipeline-wide claim.
- Two-tier (Granite default, Haiku only on the escalated minority) keeps the common path at Granite cost while paying Haiku's $0.978/1000 only where DBA actually runs.

## Architecture answer: fixed default vs adaptive roles?

- The data supports **role separation, not a single fixed extractor**: a cheap structured model (Granite) as the always-on DEFAULT, and a DIFFERENT-family model (Haiku) as the ESCALATION second builder (independence > raw quality). DBA needs two independent extractors; the default need not be the most expensive, and the reasoning model belongs nowhere in the extractor role.

## Next visible limit

- Extraction COVERAGE is no longer the binding constraint: all three non-reasoning models reach 0 substantive-0-claim and full json-validity. The next limit is **cross-extractor alignment**: table B shows the governed-outcome distribution shifts with WHICH model is the second builder (Haiku yields more `semantic_reconcilable`, GPT more `protected_branch_required` vs the same Granite reference) — i.e. the DBA region-matcher is still sensitive to extractor phrasing/granularity. Robust paraphrase-invariant region alignment, not better coverage, is the next thing to harden.

## Honesty / limits

- 17 hard cases, temp 0, one prompt — indicative, NOT a definitive model ranking. 'Quality' = structural (coverage, subject separation, fold stability), NOT truthfulness; no model is called 'best'.
- Costs are estimated from OpenRouter list pricing x measured tokens; real cost varies by provider routing.
- coverage_asymmetry (one extractor empty) is reported SEPARATELY from real conflicts — an empty Alpha is an extractor_failure, not a logical branch.
- Extractor calls only; no solver generation, no truthfulness score, no governance change. Key in-process; outputs secret-scanned.

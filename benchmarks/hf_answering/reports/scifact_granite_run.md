# Fact-verification (SciFact/FEVER-style) — tals/vitaminc / ibm-granite/granite-4.1-8b

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is NOT the claim reasoner — the model port is.

**SciFact source note:** canonical `allenai/scifact` is a deprecated dataset SCRIPT and does not load under datasets>=4; `BeIR/scifact` has no verification labels. The real evidence-style source used here is `tals/vitaminc` (real claim+evidence+3-class labels; no labels invented).

| field | value |
| --- | --- |
| dataset | `tals/vitaminc` (split `validation`) |
| model | `ibm-granite/granite-4.1-8b` (backend `openrouter`) |
| labels | SUPPORTS / REFUTES / NOT_ENOUGH_INFO |
| examples | 100 (unmapped-label rows skipped: 0) |
| answered / parse-failures / errors | 100 / 0 / 0 |
| **exact 3-class accuracy** | **0.540** (of answered) |
| elapsed | 29.08s |
| est. cost | $0.000861 |

### Gold vs predicted class distribution

| label | gold | predicted |
| --- | --- | --- |
| SUPPORTS | 31 | 63 |
| REFUTES | 28 | 36 |
| NOT_ENOUGH_INFO | 41 | 1 |

### Confusion matrix (rows = gold, cols = predicted)

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 5 | 23 | 0 |
| NOT_ENOUGH_INFO | 28 | 12 | 1 |

## Prompt (fixed, no tuning)

```
You are a fact-checking classifier. Read the EVIDENCE and decide whether it SUPPORTS the CLAIM, REFUTES the CLAIM, or gives NOT_ENOUGH_INFO. Respond with exactly one label: SUPPORTS, REFUTES, or NOT_ENOUGH_INFO.

CLAIM: {claim}

EVIDENCE: {evidence}

Label:
```

## DESi-core metrics (recorded alongside; core untouched)

| metric | value |
| --- | --- |
| replay stability | 1.0 |
| core identity | 1.0 (byte-identical) |
| governance independence | 1.0 |
| critical branch preservation | 1.0 |
| node reduction | 0.533333 |
| hard pruning (branch loss) | 0 |
| mutation attempts rejected | 5/5 |

## Honesty / limits

- One deterministic run: no retries, no answer repair, no prompt tuning, no benchmark-specific ontology. 3-class exact-match scoring on answered examples; unmapped-label rows are skipped (never relabeled).
- DESi-core metrics are intrinsic to its deterministic governance and are recorded alongside; DESi did not produce or score the verdicts.
- Any inference token is read in-process and never written to outputs.

# Micro-semantic routing — cross-summary

Algorithmic pre-solver routing: a deterministic lexical-semantic micro-layer (no LLM, no gold label, no dataset name) picks the solver prompt mode per item. Compared policies: A baseline, B benchmark-matched, C the existing DESi semantic-flow router, D the new micro-router. DeepSeek v4 Pro only, temp 0, FIXED families, same evaluator. The DESi core is untouched.

## Accuracy by policy

| dataset | A baseline | B matched | C DESi-router | D micro-router | micro policy split (base/ev/ent) |
| --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.75 | 0.79 | 0.71 | 0.73 | 47/40/13 |
| pietrolesci/nli_fever | 0.51 | 0.59 | 0.49 | 0.52 | 7/93/0 |

| dataset | overcommit A->D | overabst A->D | net vs base | net vs matched | net vs DESi-router |
| --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.512 -> 0.463 | 0.017 -> 0.085 | -2 | -6 | +2 |
| pietrolesci/nli_fever | 0.462 -> 0.308 | 0.459 -> 0.5 | +1 | -7 | +3 |

## Answers

- **Does algorithmic micro-routing help vs the fixed baseline?** tals/vitaminc: D 0.73 vs A 0.75 (-0.020); pietrolesci/nli_fever: D 0.52 vs A 0.51 (+0.010). Mixed/does not consistently beat baseline.
- **Does it beat benchmark-level prompt selection (B)?** tals/vitaminc: D 0.73 vs B 0.79 (-0.060); pietrolesci/nli_fever: D 0.52 vs B 0.59 (-0.070). NO — the dataset-matched family is >= the per-item micro-router.
- **Does it beat the existing DESi semantic-router (C)?** tals/vitaminc: D 0.73 vs C 0.71 (+0.020); pietrolesci/nli_fever: D 0.52 vs C 0.49 (+0.030). YES — the algorithmic router is >= the DESi semantic-router on both.
- **VitaminC over-commitment A->D**: 0.512 -> 0.463 (overabstention 0.017 -> 0.085).
- **FEVER over-abstention A->D**: 0.459 -> 0.5 (overcommitment 0.462 -> 0.308).
- **Does the core remain untouched?** YES — core byte-identical, replay 1.0 on every run; the micro-layer is pure string/token arithmetic outside the core.

## Which features mattered

- **VitaminC**: the micro-layer produces a real 3-way split (contradiction cues for REFUTES-like items -> baseline; high coverage + entity overlap -> entailment-direct; missing/partial coverage -> evidence-strict). Coverage + antonym/negation/numeric cues are the active signals.
- **FEVER**: hypotheses routinely introduce entities the short premise does not contain, so missing-linkage dominates and the policy collapses toward evidence-strict. Pure lexical overlap cannot detect paraphrastic entailment where surface forms differ, so it cannot target FEVER's over-abstention.

## Interpretation (per study rule)

- Where the micro-router does not beat baseline/matched, this is reported as a FEATURE GAP (lexical overlap misses paraphrastic entailment), NOT patched into the DESi core. No truthfulness claim; DESi did not solve NLI.

## Honesty / limits

- N=100/dataset; one deterministic pass; DeepSeek mild non-determinism; FIXED prompt families; micro-router is deterministic and core-independent. No core, ontology, or meaning-space change; outputs secret-scanned.

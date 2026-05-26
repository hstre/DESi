# BoolQ answering — granite (real QA benchmark on the periphery)

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is NOT the answer generator — the model port is.

| field | value |
| --- | --- |
| dataset | `google/boolq` |
| split | `validation` |
| model | `granite` (backend `openrouter`) |
| examples | 100 |
| status | **BLOCKED — no real answers produced** |
| reason | RuntimeError('OPENROUTER_API_KEY not set; OpenRouter answering unavailable (no answer is ever fabricated).') |

No answers were fabricated. Provide an inference token in-process (`OPENROUTER_API_KEY` for `--backend openrouter`, or `HF_TOKEN` for `--backend hf`) and re-run; the pipeline below is ready.

## Prompt (fixed, no tuning)

```
Answer the question with exactly one word: yes or no.

Passage: {passage}

Question: {question}

Answer:
```

## DESi-core metrics (recorded alongside; core untouched)

| metric | value |
| --- | --- |
| replay stability | 1.0 |
| core identity | 1.0 (byte-identical) |
| governance independence | 1.0 |
| critical branch preservation | 1.0 |
| node reduction | 0.533333 |
| mutation attempts rejected | 5/5 |

## Replay / core drift

- No drift: replay stable and core byte-identical to base.

## Honesty / limits

- One deterministic run: no prompt tuning, no hidden retries, no answer repair. Accuracy is exact bool match on answered examples.
- DESi-core metrics are intrinsic to its deterministic governance and are recorded alongside; DESi did not generate or score the answers.
- Any inference token is read in-process from the environment and never written to an output.

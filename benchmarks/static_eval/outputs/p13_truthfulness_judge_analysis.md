# P13 — truthfulness judge options analysis

Goal: assess whether DESi's results are distorted by the heuristic overlap scorer
(`report_truthfulqa._label`), and what a stronger judge would change. This is an
evaluation-layer study only — no intervention or SPL changes.

## The heuristic scorer we are auditing

`_label(answer, correct, incorrect)`: normalise, then **containment** (answer's
content tokens ⊆ a gold candidate) plus a difflib fuzzy ratio; **correct is
checked first**, so any sufficient overlap with a correct gold → `truthful`,
else overlap with an incorrect gold → `hallucination_suspect`. Known failure
modes (from P11/P12 forensics):

- **Asymmetric containment** scores a short answer that is a subset of a long
  gold as 1.0, even if a critical word is missing/changed (the Armstrong "for a
  man" vs "for man" miss).
- **Correct-checked-first** can label an answer truthful on partial overlap with
  a correct gold even when it is actually the incorrect variant.
- **No paraphrase understanding**: a correct answer worded unlike every gold
  string scores low and can be mislabelled `other`/hallucination.

## Judge options compared

| option | what it is | determinism | reproducible | cost | main bias risk | fixes which heuristic error | new problems |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Official TruthfulQA judge** ("GPT-judge"/"GPT-info") | GPT-3 (curie) models finetuned on the paper's human truth/info labels | deterministic at temp 0, but model-version dependent | only if the exact finetuned model is preserved | finetuning + inference $$ | trained on 2021 human labels; frozen worldview | paraphrase + critical-difference (human-aligned) | the public curie finetune is effectively deprecated/unavailable; not reproducible today without re-finetuning |
| **MC1/MC2** (TruthfulQA multiple-choice metric) | score the LM's likelihood over the provided correct vs incorrect answer strings | fully deterministic | yes (no judge model) | one forward pass per choice | none from a judge; but measures *likelihood*, not generated truth | **eliminates the matcher entirely** for the MC setting | requires the MC format + logprobs; does NOT evaluate our open-generation answers; needs provider logprob access |
| **LLM-as-judge** (GPT/Claude/DeepSeek prompt) | a strong LLM is prompted to judge answer vs gold | deterministic only at temp 0 (+ provider/version pinned) | partial — provider routing/version drift | per-call $ (×100+) | model's own beliefs; **self-preference if judge == generator family** | asymmetric containment, correct-first, paraphrase | judge ≠ ground truth; position/verbosity bias; self-confirmation if DeepSeek judges DeepSeek |
| **Embedding similarity** | cosine of sentence embeddings, answer vs gold | deterministic (fixed model) | yes (pin model) | model load; cheap after | "similar ≠ true"; threshold tuning | paraphrase / wording mismatch | semantically-similar-but-wrong (e.g. negation) scores high; needs lib + model download (absent here) |
| **Deterministic semantic / balanced-lexical scorer** | symmetric token Dice + order-sensitive ratio + exact-match priority | fully deterministic | yes | free, offline | still lexical; **self-confirmation if hand-tuned to known cases** | asymmetric containment, correct-first, exact-tie | no real paraphrase/semantic understanding; negation-blind |
| **Pairwise factuality judge** | LLM compares answer to each gold pairwise | temp-0 deterministic-ish | partial | most expensive (×gold) | order/position bias | fine-grained factual contradiction | cost; aggregation policy; same LLM biases |

## Suitability for DESi

- **MC1/MC2** is the most reproducible and bias-free, but it scores answer
  *choices*, not our open-ended generations — it would require re-running the
  benchmark in MC mode. Strong anchor, different eval mode.
- **LLM-as-judge** is the best fit for the open-generation answers we already
  have and directly attacks the matcher's paraphrase/critical-difference blind
  spots. **It must use a different-family model than the generator** (the
  generator is DeepSeek-V4, so a DeepSeek judge risks self-confirmation), at
  temperature 0, with the provider pinned for reproducibility.
- **Embedding similarity** is a cheap deterministic cross-check but is truth-blind
  (negation/critical-difference can score high); not available offline here.
- **Deterministic balanced-lexical** is what we can run with zero dependencies now;
  it removes the containment/correct-first artifacts but is not semantic, and
  carries a self-confirmation risk because its rules were informed by the known
  failure cases.

## What a stronger judge removes vs introduces

Removed (heuristic artifacts): false `truthful` from partial overlap with a
correct gold; false `hallucination` from a correct paraphrase that matches no gold
string; the exact-tie confusion between a quote and its misquote.

Introduced: judge-model belief errors and self-preference (LLM); "similar but
false" (embeddings); cost and non-determinism (LLM/pairwise); and the meta-risk
that we trade a transparent, reproducible bias for an opaque, harder-to-audit one.

## Recommendation

1. Run an **LLM-as-judge with a non-DeepSeek strong model at temp 0** as the
   primary stronger judge on the existing answers (re-evaluation, no regeneration).
2. Keep the **deterministic balanced-lexical scorer** as a free, reproducible
   cross-check and as the offline default.
3. Treat both as *instruments with bias*, not ground truth; report agreement and
   divergence, never a single "true" number.

## Honesty

- A judge is **not ground truth**; every option above has its own bias.
- LLM judges can self-confirm (especially same-family) and have verbosity/position
  bias; this must be controlled (different family, temp 0) and disclosed.
- Moving off the deterministic heuristic **loses replay-strength** (an LLM judge
  is not bit-reproducible across provider routing).
- No option here "solves" truthfulness; they shift and (hopefully) reduce bias.
